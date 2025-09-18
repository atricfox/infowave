import os
import custom_requests as requests
import json
import time
import re
import execjs
from dotenv import load_dotenv
from summary_ai import SummaryAi


class WebCliper:

    def __init__(self, env_file: str = ".env"):
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            raise ValueError("NOTION_TOKEN environment variable is required")
        self.headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-02-22",
            "Content-Type": "application/json",
        }

    def edit_articles_by_classify(self, url, classify, next_cursor=None):
        params = {
            "filter": {
                "property": "Classfiy",
                "select": {
                    'equals': classify
                }
            },
        }
        if next_cursor:
            params['start_cursor'] = next_cursor
        response = requests.post(url, headers=self.headers, data=json.dumps(params))
        res = response.json()

        for page in res['results']:
            print('summarying ' + page['properties']['Name']['title'][0]['plain_text'] + '  ' +  page['id'])
            self.only_summary_content(page['id'])
            print('汇总 ' + page['properties']['Name']['title'][0]['plain_text'] + ' 完成')
        
        if res['has_more']:
            self.edit_articles_by_classify(url, classify, res['next_cursor'])
        
        print('all done')

    def edit_articles(self, url, next_cursor=None):
        params = {
            "filter": {
                "property": "marked",
                "checkbox": {
                    'equals': False
                }
            },
        }
        if next_cursor:
            params['start_cursor'] = next_cursor
        response = requests.post(url, headers=self.headers, data=json.dumps(params))
        res = response.json()

        for page in res['results']:
            if page['properties']['marked']['checkbox']:
                print(page['properties']['Name']['title'][0]['plain_text'] + '  ' +  page['id'] + ' 已标记过，跳过')
                continue
            print('summarying ' + page['properties']['Name']['title'][0]['plain_text'] + '  ' +  page['id'])
            self.summary_content(page['id'])
            print('汇总 ' + page['properties']['Name']['title'][0]['plain_text'] + ' 完成')
        
        if res['has_more']:
            self.edit_articles(url, res['next_cursor'])
        
        print('all done')

    def edit_database(self, url):
        pages = self.edit_articles(url)
        for page in pages:
            print('summarying ' + page['properties']['Name']['title'][0]['plain_text'])
            self.summary_content(page['id'])
            print('汇总 ' + page['properties']['Name']['title'][0]['plain_text'] + ' 完成')

    def get_page_content(self, url, next_cursor=None, blocks=[]):
        params = {
            'page_size': 100
        }
        if next_cursor:
            params = {
                'start_cursor': next_cursor
            }
        response = requests.get(url, headers=self.headers, params=params)
        res = response.json()
        results = res['results']
        
        for block in results:
            if 'paragraph' in block and len(block['paragraph']['rich_text']) > 0:
                blocks.append(block['paragraph']['rich_text'][0]['plain_text'])

        if res['has_more']:
            self.get_page_content(url, res['next_cursor'], blocks)

        return blocks
    
    def only_summary_content(self, id):
        ai = SummaryAi('qwen2.5')
        url = "https://api.notion.com/v1/blocks/" + id + "/children"
        blocks = self.get_page_content(url, next_cursor=None, blocks=[])
        
        if len(blocks) == 0:
            return

        text = ''.join(blocks)
        result = ai.summary2(text)

        try:
            self.edit_summary(id, result)
        except Exception as e:
            print(e)
            print(result)

    def edit_summary(self, id, playload):
        data = {
            "properties": {
                "marked": {
                    "type": "checkbox",
                    "checkbox": True
                },
                "summary": {
                    "type": "rich_text",
                    "rich_text": [
                        {
                            "text": {
                                "content": playload,
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
                            "plain_text": re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])","",playload),
                            "href": None
                        }
                    ]
                }
            }
        }
        url = "https://api.notion.com/v1/pages/" + id
        response = requests.patch(url, headers=self.headers, data=json.dumps(data))
        return response.text

    def summary_content(self, id):
        ai = SummaryAi('qwen2.5')
        url = "https://api.notion.com/v1/blocks/" + id + "/children"
        blocks = self.get_page_content(url, next_cursor=None, blocks=[])
        
        if len(blocks) == 0:
            return

        text = ''.join(blocks)
        result = ai.summary(text)
        result = re.sub(r'^```json|`+$', '', result)

        try:
            self.edit_page(id, execjs.eval(result))
        except Exception as e:
            print(e)
            print(result)

    def edit_page(self, id, playload):
        tags = []
        for tag in playload['tags']:
            tags.append({
                "name": tag
            })
        data = {
            "properties": {
                "marked": {
                    "type": "checkbox",
                    "checkbox": True
                },
                "summary": {
                    "type": "rich_text",
                    "rich_text": [
                        {
                            "text": {
                                "content": playload['summary'],
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
                            "plain_text": re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])","",playload['summary']),
                            "href": None
                        }
                    ]
                },
                "labels": {
                    "type": "multi_select",
                    "multi_select": tags
                }
            }
        }
        url = "https://api.notion.com/v1/pages/" + id
        response = requests.patch(url, headers=self.headers, data=json.dumps(data))
        return response.text


    def edit_articles_classify(self, url, next_cursor=None):
        params = {
            "filter": {
                "property": "Classfiy",
                "select": {
                    'is_empty': True
                }
            },
        }
        if next_cursor:
            params['start_cursor'] = next_cursor
        response = requests.post(url, headers=self.headers, data=json.dumps(params))
        res = response.json()

        for page in res['results']:
            name = page['properties']['Name']['title'][0]['plain_text']
            labels = []
            for label in page['properties']['labels']['multi_select']:
                labels.append(label['name'])
            print('Classifying ' + name )
            text = '记录的标题为：' + name + '，标签为：' + ','.join(labels)
            self.classify_page(page['id'], text)
        
        if res['has_more']:
            self.edit_articles_classify(url, res['next_cursor'])
        
        print('all done')

    def classify_page(self, id, text):
        ai = SummaryAi('llama3.1')
        categories = ['区块链', 
        'ChatGPT', 
        'SEO', 
        'Web3', 
        'Web开发', 
        '编程语言', 
        '餐饮', 
        '产品开发', 
        '创业', 
        '独立开发', 
        '个人管理', 
        '公开课', 
        '管理', 
        '家庭', 
        '健康', 
        '经济学', 
        '开源软件', 
        '历史', 
        '量化投资', 
        '临床试验', 
        '领导力', 
        '软件开发', 
        '社会', 
        '生命科学', 
        '生物统计', 
        '书籍', 
        '数据科学', 
        '数学', 
        '思维', 
        '算法', 
        '统计学', 
        '投资理财', 
        '团队管理', 
        '外语学习', 
        '销售', 
        '效率效能', 
        '协作', 
        '心理学', 
        '学习', 
        '医药研发', 
        '移动开发', 
        '移民', 
        '英语学习', 
        '育儿', 
        '远程工作', 
        '自媒体', 
        '软件推荐', 
        '前端开发', 
        '写作', 
        '教育', 
        '金融', 
        '自我提升', 
        '阅读', 
        '自然科学', 
        '科普', 
        '生命科学', 
        '其他', 
        '艺术',
        'Python',
        'Golang',
        'PHP',
        'Nodejs'
        'JavaScript',
        'Vue',
        'React',
        'Nextjs']

        result = ai.classify(text + '，请综合分析标题和标签，将记录分类为以下类别之一：' + ','.join(categories) + '。')
        result = re.sub(r'分类名称：|分类：|分类为：|分类为:|分类:|分类名称:', '', result)

        print('分类为 ' + result)

        try:
            self.edit_page_classify(id, result)
            print('----------------分类完成--------------')
        except Exception as e:
            print(e)
            print(result)

    def edit_page_classify(self, id, playload):
        data = {
            "properties": {
                "Classfiy": {
                    "select": {
                        "name": playload
                    }
                }
            }
        }
        url = "https://api.notion.com/v1/pages/" + id
        response = requests.patch(url, headers=self.headers, data=json.dumps(data))
        return response.text

if __name__ == "__main__":
    cliper = WebCliper()
    url = "https://api.notion.com/v1/databases/49876327f45048f7ac6c4f78b39a2ffc/query"
    cliper.edit_articles_by_classify(url, '软件开发')
    # 独立开发
    # 学习
    # 学习方法
    # 思维
    # 效率效能
    # 个人管理

    # cliper.edit_articles(url)
    # result = cliper.get_articles(url)
    # print(result)
    # cliper = WebCliper("https://api.notion.com/v1/pages/2ca214d6-fefa-4a1c-8fa4-20c81b5c2c83")
    # url = "https://api.notion.com/v1/blocks/2ca214d6-fefa-4a1c-8fa4-20c81b5c2c83/children?page_size=100"
    # print(cliper.summary_content(url))
    # url = "https://api.notion.com/v1/pages/2ca214d6-fefa-4a1c-8fa4-20c81b5c2c83"
    # print(cliper.get_page(url))
