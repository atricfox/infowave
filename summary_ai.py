import ollama

class SummaryAi:

    def __init__(self, model='gemma2:27b'):
        self.model = model
    
    def summary2(self, text):
        # prompt = '''
        # 请用中文帮我按照下面格式详细汇总上面文章的主旨和主要内容。
        # 主题：[请在此处填写文章的主题，例如“人工智能在医疗行业的应用”]
        # 主旨：[请简要说明汇总的主旨和目的，例如“为医疗行业从业者提供最新的人工智能技术动态”]
        # 目标读者：[请描述目标读者群体，例如“医疗行业专业人士、科研人员、政策制定者”]
        # 关键词：[列出与主题紧密相关的关键词，如“AI、机器学习、医疗诊断、远程医疗服务”]
        # 内容要求：
        # 概述：对所选主题进行简短的介绍，包括背景信息、重要性和研究现状。
        # 主要发现/观点：总结几篇关键文章的主要观点或研究成果，确保涵盖不同的视角。
        # 字数限制：字数在500-100字之间
        # '''
        prompt = '''
        请用中文帮我按照下面格式详细汇总上面文章的主旨和主要内容。
        字数限制：字数在500-100字之间
        '''
        prompt = text + '\n' + prompt
        response = ollama.generate(
            model = self.model,
            prompt = prompt,
            options = {
                'seed': 0
            }
        )
        return response['response']
    
    def summary(self, text):
        prompt = '请帮我使用一短话简要汇总上面文章的主要内容，不需要分汇总，并给出文章的tags。结果输出为严格的json格式字符串，不需要增加json代码标识，自动对输出格式按照json标准校验，并修正输出格式，其中内容汇总的key为summary，tags的key为tags。输出结果的json字符串格式如下：{"summary": "xxx", "tags": ["xxx", "xxx"]}。summary和tags的值不能携带双引号，有需要自动转成单引号。直接输出最终结果即可，不要输出中间过程。'
        prompt = text + '\n' + prompt
        response = ollama.generate(
            model = self.model,
            prompt = prompt,
            options = {
                'seed': 0
            }
        )
        return response['response']
        
    def classify(self, text):
        prompt = '如果可能，请帮我选择一个最合适的分类，并输出分类的名称，如果无法判断合适的分类，请输出分类为其他。输出的结果为简单的分类名称，不要输出其他任何信息。'
        prompt = text + '\n' + prompt
        response = ollama.generate(
            model = self.model,
            prompt = prompt,
            options = {
                'seed': 0
            }
        )
        return response['response']
        