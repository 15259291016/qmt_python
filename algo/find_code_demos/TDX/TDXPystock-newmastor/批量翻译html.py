# -*- coding: utf-8 -*-
'''
author: newhackerman
说明：此代码的功能是调用google api  v2 版本 ，批量翻译多个html文档，翻译文本，翻译单个html文档，或在线的单个html文档 ，
例如:某些帮助文档全是英文或其它语言，这个代码也许能帮到你
某些英语/或其它语言的 chm文档 可使用CHM Editor 将文档导出工程，然后将工程目录下的html，批量翻译，然后再保存
一次最多翻译5000行
'''
from get_config import get_config
from google.cloud import translate
from bs4 import BeautifulSoup
import googleapiclient.discovery  #pip install google-api-python-client
import requests as req
import os
import socket
import socks
import time

# 设置socks5代理 ,使用https代理连不上 google
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 10808)
socket.socket = socks.socksocket #使用socks建立连接

config = get_config()
googlefanyi_apikey = config['googlefanyi_apikey']
# 创建 Google 翻译服务对象
service = googleapiclient.discovery.build('translate', 'v2', developerKey=googlefanyi_apikey)
# 创建 Google 翻译客户端
client = translate.TranslationServiceClient(credentials=googlefanyi_apikey)


# 设置全局代理
# os.environ["HTTP_PROXY"] = 'https://127.0.0.1:10809'
# os.environ["HTTPS_PROXY"] = 'https://127.0.0.1:10809'
# os.environ['ALL_PROXY'] = 'https://127.0.0.1:10809'
# os.environ['ALL_PROXY'] = 'socks5h://127.0.0.1:10808'
def google_translatehtmls(sdir, tdir, dest):
    """
    遍历一个目录下的所有HTML文件，并使用Google翻译API将其翻译成目标语言。
    :param sdir: 源语言文件所在的目录路径。
    :param tdir: 目标语言文件输出的目录路径。
    :param dest: 要翻译的目标语言
    LANGUAGES = {
    'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'he': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'or': 'odia',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'ug': 'uyghur',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu',
    :return: None
    """
    # 获取要翻译的 HTML 文件的目录
    input_dir = sdir
    # 获取要保存翻译后 HTML 文件的目录
    output_dir = tdir
    # 创建目标目录（如果不存在）
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 遍历要翻译的 HTML 文件
    for filename in os.listdir(input_dir):
        # 获取文件的完整路径
        try:
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            google_translatehtml(input_path, output_path, dest)
        except BaseException as b:
            print("处理文件：%s 失败" % input_path)
            continue
        time.sleep(0.2)

def google_translatehtml(htmlfile, output_path, dest):
    """
    翻译html文件
    :param htmlfile: html文件路径
    :param output_path: 输出路径
    :param dest: 目标语言
    :return:
    """

    if not os.path.exists(htmlfile):
        print("文件不存在")
        return
    input_path = htmlfile
    endwiths=[".html",".htm",".md",".txt",".doc",".docx",".pdf"]
    retext=''
    for endwith in endwiths:
        if input_path.endswith(endwith):
            print(input_path)
              # 打开要翻译的 HTML 文件
            html = None
            try:
                with open(input_path, "r", encoding='utf-8') as f:
                    html = f.readlines()
            except BaseException as b:
                print("文件读取失败")
                return
            lines=len(html)
            step=int(lines/5000)+1
            if step==1:
                try:
                    with open(input_path, "r", encoding='utf-8') as f:
                        html = f.read()
                except BaseException as b:
                    print("文件读取失败")

                trys = 0
                while trys < 5:
                    try:
                        retext = google_translate_text(html, dest)
                        break
                    except BaseException as b:
                        trys += 1
                        print(f"翻译失败,开始第{trys}重试")
                        continue
                if retext is None:
                    return
            else:
                for i in range(step):
                    if i==step-1:
                        tmp=html[i*5000:]
                    else:
                        tmp=html[i*5000:(i+1)*5000]

                # 使用 BeautifulSoup 解析 HTML
                #现google支持直接把html扔进去，自动翻译内容，不需要人工解释标签 文本
                    trys=0
                    while trys<5:
                        try:
                            retext+=google_translate_text(tmp, dest)
                            break
                        except BaseException as b:
                            trys += 1
                            print(f"翻译失败,开始第{trys}重试")
                            continue
        else:
            continue

    if retext !='' or retext is not None:
        with open(output_path, "w", encoding='utf-8') as f:
            f.write(retext)

def sigle_tag_translate(htmlfile,output_path, dest):

    soup = BeautifulSoup(htmlfile, "lxml")
    # 查找所有需要翻译的文本
    texts = soup.find_all(string=True)  # 查找html中的所有标记
    # 翻译文本
    for text in texts:
        if text.strip()=='' or len(text) < 2 or text is None or text == '\n':
            continue
        # print('待翻译文本 :%s' % text)
        # 翻译文本
        try:
            retext = google_translate_text(text, dest)
            # print('翻译后的文本：%s' %retext)
            text.replace_with(text + '\t#' + retext) #原文加上翻译后的文本
        except BaseException as b:
            continue

    # 将翻译后的 HTML 保存到文件
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(soup.prettify())

def google_translate_text(text, dest):
    """
    使用Google翻译API翻译文本。

    参数:
    text: 要翻译的文本，类型为字符串。
    dest:目标语言

    返回值:
    翻译后的文本，类型为字符串。
    """
    # 翻译文本
    try:
        result = service.translations().list(q=text, target=dest, source='').execute()  # v2 版本 source :指定原语言
        # 调用的url: https://translation.googleapis.com/language/translate/v2?q=hello+world&target=zh-cn&source='en'&key=AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw&alt=json
        retext = result['translations'][0]['translatedText']  # v2 版本
        # result = client.translate_text(
        #     request={
        #         "parent": '',
        #         "contents": [text],
        #         "mime_type": "text/plain",  # mime types: text/plain, text/html
        #         "source_language_code": "en-US",
        #         "target_language_code": dest,
        #     }
        # )
        # for translation in result.translations:
        #     print(f"Translated text: {translation.translated_text}")

        # retext=result['translations'][0]['translated_text'] #v3 版本
        # print('翻译后的文本：%s' %retext)
        return retext
    except BaseException as b:
        if 'timed out' in str(b): #重试一次
            print('翻译超时')
            try:
                result = service.translations().list(q=text, target=dest, source='').execute()  # v2 版本 source :指定原语言
                retext = result['translations'][0]['translatedText']  # v2 版本
                return retext
            except BaseException as b:
                print('翻译超时')
                return
        return


# 翻译在线的html文件

def google_translatehtml_url(url, tdir, dest):
    """
    翻译在线的html文件
    :param sdir: html文件路径
    :param tdir: 输出路径
    :param dest: 目标语言
    :return:
    """
    # 获取要翻译的 HTML url
    url = url
    html=None
    # proxies={'socks':'socks5h://127.0.0.1:10808'}

    try:
        html = req.get(url, timeout=30).content.decode('utf-8')
    except BaseException as b:
        print("url请未失败")
        print(b)
        try:
            html = req.get(url, timeout=30).content.decode('utf-8')
        except BaseException as b:
            print("url请未失败")
            return
    # print(html)
    # 获取要保存翻译后 HTML 文件的目录
    output_dir = tdir

    # 创建目标目录（如果不存在）
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        # 使用 BeautifulSoup 解析 HTML

    retext = google_translate_text(html, dest)
    if retext is None:
    		
        
        print('翻译返回数据为空')
        return
    # print(retext)

    urlb=url.split('//')[1]
    if urlb.find('/')>0:
        urlb=urlb.split('/')[0]
    filename = f'{urlb}_{dest}.html'
    output_path = os.path.join(output_dir, filename)
    # 将翻译后的 HTML 保存到文件
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(retext)
    # 在浏览器中打开
    from conventfilepathToURI import conventfilepathToURI  # 将文件路径转成url
    from mainconfig import chromePath

    fileurl = conventfilepathToURI(output_path)  # 将本地文件转URL
    print(fileurl)
    # 指定本定的浏览器
    import webbrowser  # 打开浏览器
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chromePath))
    webbrowser.get('chrome').open(fileurl, new=1, autoraise=True)

# def google_translatehtml_url(url, tdir, dest):
#     """
#     翻译在线的html文件
#     :param sdir: html文件路径
#     :param tdir: 输出路径
#     :param dest: 目标语言
#     :return:
#     """
#     result= client.translate_website(
#         url, target_language=dest
#     )
#     retext=result["translated_url"]
#     if retext is None:
#         return



if __name__ == '__main__':
    print('支持的语言：')
    languages=''''af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'he': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'or': 'odia',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'ug': 'uyghur',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu'
    '''
    print(languages)
    print('请选择翻译功能，1、翻译文本 2、翻译单个html 3、翻译在线url页面，4、批量翻译')

    select=input('请输入：\n')
    if select=='1':
        print('翻译文本\n')
        while True:
            text=input('请输入要翻译的文本：\n')
            dest=input('请输入目标语言：\n')
            if dest=='':
                dest='zh-cn'
            result=google_translate_text(text,dest)
            print(result)
            select=input('是否继续翻译，y/n\n')
            if select=='y':
                continue
            else:
                exit()
    elif select=='2':
        print('翻译单个html\n')
        while True:
            sdir=input('请输入html文件路径：\n')
            tdir = input('请输入翻译后存放目录：\n')
            dest=input('请输入目标语言：\n')
            google_translatehtml(sdir,tdir,dest)
            select=input('是否继续翻译，y/n\n')
            if select=='y':
                continue
            else:
                exit()

    elif select=='3':
        print('翻译在线html页面\n')
        while True:
            url=input('请输入要翻译的html页面url：\n')
            tdir= input('请输入翻译后存放目录：\n')
            if tdir=='':
                tdir=os.getcwd()
            dest=input('请输入目标语言：\n')
            if dest=='':
                dest='zh-cn'
            google_translatehtml_url(url,tdir,dest)
            select=input('是否继续翻译，y/n\n')
            if select=='y':
                continue
            else:
                exit()
    elif select=='4':
        print('批量翻译html文档\n')
        sdir=input('请输入html文档源目录：\n')

        tdir = input('请输入翻译后存放目录：\n')
        google_translatehtmls(sdir,tdir, 'zh-cn')
    else:
        print('输入错误')


    # result=google_translate_text('hello world', 'zh-cn')
    # print(result)
