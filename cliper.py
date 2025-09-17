import json
import os
import re
import time
from typing import Optional

import requests

from glm_ai import GlmAi


class Cliper:
    def __init__(self, env_file: Optional[str] = ".env"):
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            raise ValueError("NOTION_TOKEN environment variable is required")
        self.headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-02-22",
            "Content-Type": "application/json",
        }
        self.ai = GlmAi(env_file=env_file)
        self.categories = [
            '区块链', 'ChatGPT', 'SEO', 'Web3', 'Web开发', '编程语言', '餐饮', '产品开发', '创业',
            '独立开发', '个人管理', '公开课', '管理', '家庭', '健康', '经济学', '开源软件', '历史',
            '量化投资', '临床试验', '领导力', '软件开发', '社会', '生命科学', '生物统计', '书籍',
            '数据科学', '数学', '思维', '算法', '统计学', '投资理财', '团队管理', '外语学习',
            '销售', '效率效能', '协作', '心理学', '学习', '医药研发', '移动开发', '移民', '英语学习',
            '育儿', '远程工作', '自媒体', '软件推荐', '前端开发', '写作', '教育', '金融', '自我提升',
            '阅读', '自然科学', '科普', '生命科学', '其他', '艺术', 'Python', 'Golang', 'PHP', 'Nodejs',
            'JavaScript', 'Vue', 'React', 'Nextjs'
        ]

    def update_web_clips(self, url, next_cursor=None):
        params = {
            "filter": {
                "property": "updated",
                "checkbox": {
                    "equals": False
                }
            }
        }
        if next_cursor:
            params['start_cursor'] = next_cursor

        payload = self._request_json(url, params, method="POST")
        results = payload.get('results', [])
        if not results:
            print('没有可处理的记录')
            return

        for page in results:
            self._process_page(page)

        if payload.get('has_more'):
            self.update_web_clips(url, payload.get('next_cursor'))

    def update_single_clip(self, page_id: str):
        page_url = f"https://api.notion.com/v1/pages/{page_id}"
        page = self._request_json(page_url, method="GET")
        if not page:
            print('未获取到页面信息')
            return
        self._process_page(page)

    def _get_page_name(self, page):
        title = (page.get('properties', {})
                     .get('Name', {})
                     .get('title', []))
        if title:
            return title[0].get('plain_text', '未命名')
        return '未命名'

    def _get_summary_text(self, page):
        summary_prop = (page.get('properties', {})
                            .get('summary', {})
                            .get('rich_text', []))
        summary_text = ''.join(item.get('plain_text', '') for item in summary_prop).strip()
        return summary_text

    def _generate_tags_and_summary(self, summary_text):
        try:
            result = self.ai.generate_summary_and_tags(summary_text)
        except ValueError as exc:
            print(f"GLM 生成标签失败: {exc}")
            return [], summary_text

        tags = result.get('tags') if isinstance(result, dict) else []
        if not isinstance(tags, list):
            tags = []
        unique_tags = []
        for tag in tags:
            if isinstance(tag, str) and tag and tag not in unique_tags:
                unique_tags.append(tag)

        summary = result.get('summary') if isinstance(result, dict) else summary_text
        if not isinstance(summary, str) or not summary.strip():
            summary = summary_text
        return unique_tags, summary.strip()

    def _generate_classify(self, summary_text, tags):
        try:
            result = self.ai.classify(summary_text, tags, self.categories)
        except ValueError as exc:
            print(f"GLM 分类失败: {exc}")
            return ''

        result = re.sub(r'分类名称：|分类：|分类为：|分类为:|分类:|分类名称:', '', result)
        result = result.strip()
        if not result:
            return ''
        if result not in self.categories:
            return '其他'
        return result

    def _update_page(self, page_id, tags, classify):
        properties = {}
        if tags:
            tag_text = ','.join(tags)
            properties['Tags'] = {
                "type": "rich_text",
                "rich_text": [
                    {
                        "text": {
                            "content": tag_text,
                            "link": None
                        },
                        "annotations": {
                            "bold": False,
                            "italic": False,
                            "strikethrough": False,
                            "underline": False,
                            "code": False,
                            "color": "default"
                        },
                        "plain_text": tag_text,
                        "href": None
                    }
                ]
            }
        properties['Classfiy'] = {
            "select": {
                "name": classify or '其他'
            }
        }
        properties['updated'] = {
            "type": "checkbox",
            "checkbox": True
        }

        data = {"properties": properties}
        url = f"https://api.notion.com/v1/pages/{page_id}"
        self._request_json(url, data, method="PATCH")

    def _request_json(self, url: str, payload: Optional[dict] = None, method: str = "POST") -> dict:
        method = method.upper()
        headers = self.headers.copy()
        data = payload if payload is not None else {}

        attempt = 0
        while True:
            attempt += 1
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=60)
                elif method == "PATCH":
                    response = requests.patch(url, headers=headers, json=data, timeout=60)
                else:
                    response = requests.post(url, headers=headers, json=data, timeout=60)
                response.raise_for_status()
                body = response.text
                if not body:
                    return {}
                return json.loads(body)
            except requests.HTTPError as exc:
                resp = exc.response
                detail = resp.text if resp else str(exc)
                status = resp.status_code if resp else 'unknown'
                raise RuntimeError(f"Notion API 请求失败 {status}: {detail}") from exc
            except requests.RequestException as exc:
                reason = getattr(exc, 'reason', None) or str(exc)
                message = str(reason)
                wait_time = min(5, attempt)
                print(f"请求异常({message})，第 {attempt} 次重试，等待 {wait_time} 秒")
                time.sleep(wait_time)
                continue

    def _process_page(self, page: dict) -> None:
        name = self._get_page_name(page)
        if self._is_marked_updated(page):
            print(f"{name} 已更新过，跳过")
            return
        summary_text = self._get_summary_text(page)
        if not summary_text:
            print(f"{name} 缺少 summary，跳过")
            return

        tags, summary = self._generate_tags_and_summary(summary_text)
        classify = self._generate_classify(summary, tags)

        if not tags and not classify:
            print(f"{name} 生成标签和分类失败，跳过")
            return

        print(f"更新 {name} 的标签和分类")
        self._update_page(page['id'], tags, classify)

    def _is_marked_updated(self, page: dict) -> bool:
        properties = page.get('properties', {}) if isinstance(page, dict) else {}
        updated_prop = properties.get('updated') if isinstance(properties, dict) else None
        if isinstance(updated_prop, dict):
            checkbox = updated_prop.get('checkbox')
            if checkbox is not None:
                return bool(checkbox)
            if updated_prop.get('type') == 'checkbox':
                return bool(updated_prop.get('checkbox'))
        return False
