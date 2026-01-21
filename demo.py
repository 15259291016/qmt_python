#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 drissionPage 和 Chrome 浏览器实现 i问财网站的关键词查询
查询: 2025年12月24日603060.SH的DDE散户数量指标
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from time import sleep, time
from urllib.parse import quote
from datetime import datetime

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    print("请先安装 DrissionPage: pip install DrissionPage")
    sys.exit(1)

# 配置日志（仅错误级别）
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 指定的 XPath 路径
SPECIFIC_XPATH = "/html/body/div[1]/div[2]/div[2]/div[1]/div/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div/div[2]/div/div/div/p/span"


def extract_xpath_content(page: ChromiumPage, xpath: str = SPECIFIC_XPATH) -> Optional[str]:
    """
    提取指定 XPath 的元素内容
    
    Args:
        page: ChromiumPage 对象
        xpath: XPath 路径，默认为指定的路径
        
    Returns:
        Optional[str]: 元素文本内容，如果未找到则返回 None
    """
    try:
        element = page.ele(f'xpath:{xpath}', timeout=3)
        if element:
            return element.text
        return None
    except:
        return None


def query_iwencai(
    query_text: str,
    browser_path: Optional[str] = None,
    headless: bool = False,
    wait_time: int = 5,
    use_url_param: bool = True
) -> Dict[str, Any]:
    """
    使用 drissionPage 在 i问财网站查询关键词
    
    Args:
        query_text: 查询关键词，例如："2025年12月24日603060.SH的DDE散户数量指标"
        browser_path: Chrome 浏览器路径，如果为 None 则使用系统默认路径
        headless: 是否使用无头模式（不显示浏览器窗口）
        wait_time: 等待页面加载的时间（秒）
        use_url_param: 是否使用 URL 参数直接查询（推荐方式，更简单可靠）
        
    Returns:
        Dict[str, Any]: 包含查询结果的字典，包含以下字段：
            - success: 是否成功
            - query_text: 查询文本
            - url: 查询后的页面URL
            - result_text: 结果文本内容
            - error: 错误信息（如果有）
    """
    page = None
    try:
        # 配置浏览器选项
        co = ChromiumOptions()
        
        # 如果指定了浏览器路径，则设置
        if browser_path:
            co.set_browser_path(browser_path)
        
        # 设置是否无头模式
        if headless:
            co.headless(True)
        else:
            co.headless(False)
        
        # 创建浏览器页面对象
        logger.info("正在启动 Chrome 浏览器...")
        page = ChromiumPage(co)
        
        # 方式1：直接通过 URL 参数查询（推荐，更简单可靠）
        if use_url_param:
            # URL 编码查询关键词
            encoded_query = quote(query_text)
            query_url = f'https://www.iwencai.com/unifiedwap/result?w={encoded_query}'
            
            page.get(query_url)
            
            # 获取当前页面URL
            current_url = page.url
            
            # 尝试获取查询结果
            result_text = ""
            result_selectors = [
                '.result-container',
                '.query-result',
                '.table-container',
                'table',
                '.data-table',
                '.result-table',
                '.stock-table',
                'xpath://div[contains(@class, "result")]',
                'xpath://table',
            ]
            
            for selector in result_selectors:
                try:
                    result_elements = page.eles(selector, timeout=2)
                    if result_elements:
                        result_text = "\n".join([elem.text for elem in result_elements if elem.text])
                        if result_text:
                            break
                except:
                    continue
            
            # 如果没找到特定结果元素，获取整个页面文本
            if not result_text:
                result_text = page.html
            
            # 提取指定 XPath 的内容
            xpath_content = extract_xpath_content(page)
            
            # 打印 XPath 内容
            print(f"\n{'='*60}")
            print(f"【XPath 提取结果】")
            print(f"{'='*60}")
            print(f"查询: {query_text}")
            print(f"XPath: {SPECIFIC_XPATH}")
            if xpath_content:
                print(f"内容: {xpath_content}")
            else:
                print("内容: (未找到)")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'query_text': query_text,
                'url': current_url,
                'result_text': result_text[:5000] if len(result_text) > 5000 else result_text,  # 限制长度
                'xpath_content': xpath_content,  # 添加 XPath 内容
                'error': None
            }
        
        # 方式2：模拟操作（备选方案）
        page.get('https://www.iwencai.com/')
        
        # 尝试多种方式定位搜索框
        search_box = None
        search_selectors = [
            'input[placeholder*="问题"]',
            'input[placeholder*="请输入"]',
            'input[type="text"]',
            '.search-input',
            '#search-input',
            'input.search-input',
            'textarea[placeholder*="问题"]',
        ]
        
        for selector in search_selectors:
            try:
                search_box = page.ele(selector, timeout=2)
                if search_box:
                    break
            except:
                continue
        
        if not search_box:
            try:
                search_box = page.ele('xpath://input[contains(@placeholder, "问题") or contains(@placeholder, "请输入")]')
            except:
                pass
        
        if not search_box:
            raise Exception("无法找到搜索框，请检查网站结构是否发生变化")
        
        # 清空搜索框并输入查询内容
        search_box.clear()
        search_box.input(query_text)
        
        # 尝试多种方式定位搜索按钮
        search_button = None
        button_selectors = [
            'button:contains("搜索")',
            'button:contains("查询")',
            'button.search-btn',
            '.search-btn',
            'button[type="submit"]',
            'xpath://button[contains(text(), "搜索") or contains(text(), "查询")]',
        ]
        
        for selector in button_selectors:
            try:
                search_button = page.ele(selector, timeout=2)
                if search_button:
                    break
            except:
                continue
        
        if not search_button:
            search_box.input('\n')
        else:
            search_button.click()
        
        # 获取当前页面URL
        current_url = page.url
        
        # 尝试获取查询结果
        result_text = ""
        result_selectors = [
            '.result-container',
            '.query-result',
            '.table-container',
            'table',
            '.data-table',
            '.result-table',
            'xpath://div[contains(@class, "result")]',
        ]
        
        for selector in result_selectors:
            try:
                result_elements = page.eles(selector, timeout=2)
                if result_elements:
                    result_text = "\n".join([elem.text for elem in result_elements if elem.text])
                    if result_text:
                        break
            except:
                continue
        
        # 如果没找到特定结果元素，获取整个页面文本
        if not result_text:
            result_text = page.html
        
        return {
            'success': True,
            'query_text': query_text,
            'url': current_url,
            'result_text': result_text[:5000] if len(result_text) > 5000 else result_text,  # 限制长度
            'error': None
        }
        
    except Exception as e:
        logger.error(f"查询过程中发生错误: {e}", exc_info=True)
        return {
            'success': False,
            'query_text': query_text,
            'url': page.url if page else None,
            'result_text': None,
            'xpath_content': None,
            'error': str(e)
        }
    finally:
        if page:
            pass
            # page.quit()  # 如果需要自动关闭，取消注释


def query_iwencai_batch(
    query_list: List[str],
    browser_path: Optional[str] = None,
    headless: bool = False,
    wait_time: int = 5,
    use_url_param: bool = True,
    reuse_browser: bool = True
) -> List[Dict[str, Any]]:
    """
    批量查询多个关键词
    
    Args:
        query_list: 查询关键词列表，例如：["比亚迪散户指标", "中国银行散户指标"]
        browser_path: Chrome 浏览器路径，如果为 None 则使用系统默认路径
        headless: 是否使用无头模式（不显示浏览器窗口）
        wait_time: 每个查询等待页面加载的时间（秒）
        use_url_param: 是否使用 URL 参数直接查询（推荐方式，更简单可靠）
        reuse_browser: 是否复用浏览器实例（True 时只启动一次浏览器，False 时每个查询都重启）
        
    Returns:
        List[Dict[str, Any]]: 查询结果列表，每个元素与 query_iwencai 返回格式相同
    """
    results = []
    page = None
    
    try:
        # 配置浏览器选项
        co = ChromiumOptions()
        
        if browser_path:
            co.set_browser_path(browser_path)
        
        if headless:
            co.headless(True)
        else:
            co.headless(False)
        
        # 如果复用浏览器，只启动一次
        if reuse_browser:
            page = ChromiumPage(co)
        
        # 遍历查询列表
        for idx, query_text in enumerate(query_list, 1):
            # 如果不复用浏览器，每个查询都创建新实例
            if not reuse_browser:
                page = ChromiumPage(co)
            
            try:
                if use_url_param:
                    # URL 编码查询关键词
                    encoded_query = quote(query_text)
                    query_url = f'https://www.iwencai.com/unifiedwap/result?w={encoded_query}'
                    
                    page.get(query_url)
                    
                    # 获取当前页面URL
                    current_url = page.url
                    
                    # 尝试获取查询结果
                    result_text = ""
                    result_selectors = [
                        '.result-container',
                        '.query-result',
                        '.table-container',
                        'table',
                        '.data-table',
                        '.result-table',
                        '.stock-table',
                        'xpath://div[contains(@class, "result")]',
                        'xpath://table',
                    ]
                    
                    for selector in result_selectors:
                        try:
                            result_elements = page.eles(selector, timeout=2)
                            if result_elements:
                                result_text = "\n".join([elem.text for elem in result_elements if elem.text])
                                if result_text:
                                    break
                        except:
                            continue
                    
                    # 如果没找到特定结果元素，获取整个页面文本
                    if not result_text:
                        result_text = page.html
                    
                    # 提取指定 XPath 的内容
                    xpath_content = extract_xpath_content(page)
                    
                    # 打印 XPath 内容
                    print(f"\n{'='*60}")
                    print(f"【XPath 提取结果 - 查询 {idx}/{len(query_list)}】")
                    print(f"{'='*60}")
                    print(f"查询: {query_text}")
                    print(f"XPath: {SPECIFIC_XPATH}")
                    if xpath_content:
                        print(f"内容: {xpath_content}")
                    else:
                        print("内容: (未找到)")
                    print(f"{'='*60}\n")
                    
                    results.append({
                        'success': True,
                        'query_text': query_text,
                        'url': current_url,
                        'result_text': result_text[:5000] if len(result_text) > 5000 else result_text,
                        'xpath_content': xpath_content,  # 添加 XPath 内容
                        'error': None
                    })
                else:
                    results.append({
                    'success': False,
                    'query_text': query_text,
                    'url': None,
                    'result_text': None,
                    'xpath_content': None,
                    'error': '批量查询暂不支持模拟操作方式'
                })
            
            except Exception as e:
                results.append({
                    'success': False,
                    'query_text': query_text,
                    'url': page.url if page else None,
                    'result_text': None,
                    'xpath_content': None,
                    'error': str(e)
                })
            
            finally:
                # 如果不复用浏览器，每个查询后关闭
                if not reuse_browser and page:
                    page.quit()
                    page = None
            
            # 查询间隔，避免请求过快
            if idx < len(query_list):
                # sleep(1)
                pass
        
    except Exception as e:
        logger.error(f"批量查询过程中发生错误: {e}", exc_info=True)
    finally:
        if reuse_browser and page:
            pass
            # page.quit()  # 如果需要自动关闭，取消注释
    
    return results


def loop_query_test(
    query_list: List[str],
    loop_count: int = 100,
    interval: float = 2.0,
    browser_path: Optional[str] = None,
    headless: bool = False,
    wait_time: int = 5,
    use_url_param: bool = True
) -> Dict[str, Any]:
    """
    循环查询测试
    
    Args:
        query_list: 查询关键词列表
        loop_count: 循环次数
        interval: 每次查询之间的间隔（秒）
        browser_path: Chrome 浏览器路径
        headless: 是否使用无头模式
        wait_time: 每个查询等待页面加载的时间（秒）
        use_url_param: 是否使用 URL 参数直接查询
        
    Returns:
        Dict[str, Any]: 统计信息
    """
    print("=" * 60)
    print("循环查询测试")
    print("=" * 60)
    print(f"查询列表: {query_list}")
    print(f"循环次数: {loop_count}")
    print(f"查询间隔: {interval} 秒")
    print(f"总查询次数: {len(query_list) * loop_count}")
    print("=" * 60)
    print()
    
    # 统计信息
    stats = {
        'total_queries': 0,
        'success_count': 0,
        'fail_count': 0,
        'results': [],
        'start_time': datetime.now(),
        'end_time': None
    }
    
    page = None
    try:
        # 配置浏览器选项
        co = ChromiumOptions()
        if browser_path:
            co.set_browser_path(browser_path)
        if headless:
            co.headless(True)
        else:
            co.headless(False)
        
        # 启动浏览器
        page = ChromiumPage(co)
        
        # 循环查询
        for loop_idx in range(1, loop_count + 1):
            print(f"\n{'='*60}")
            print(f"第 {loop_idx}/{loop_count} 轮循环")
            print(f"{'='*60}")
            
            for query_idx, query_text in enumerate(query_list, 1):
                stats['total_queries'] += 1
                query_num = (loop_idx - 1) * len(query_list) + query_idx
                
                print(f"\n[查询 {query_num}/{len(query_list) * loop_count}] {query_text}")
                
                try:
                    # URL 编码查询关键词
                    encoded_query = quote(query_text)
                    query_url = f'https://www.iwencai.com/unifiedwap/result?w={encoded_query}'
                    
                    page.get(query_url)
                    
                    current_url = page.url
                    
                    # 提取 XPath 内容
                    xpath_content = extract_xpath_content(page)
                    
                    # 尝试获取结果
                    result_text = ""
                    result_selectors = [
                        '.result-container',
                        '.query-result',
                        '.table-container',
                        'table',
                        '.data-table',
                        '.result-table',
                        '.stock-table',
                    ]
                    
                    for selector in result_selectors:
                        try:
                            result_elements = page.eles(selector, timeout=2)
                            if result_elements:
                                result_text = "\n".join([elem.text for elem in result_elements if elem.text])
                                if result_text:
                                    break
                        except:
                            continue
                    
                    if not result_text:
                        result_text = page.html[:1000] if page.html else ""
                    
                    # 判断是否成功
                    success = bool(result_text or xpath_content)
                    
                    if success:
                        stats['success_count'] += 1
                        status = "✅ 成功"
                    else:
                        stats['fail_count'] += 1
                        status = "❌ 失败"
                    
                    print(f"状态: {status}")
                    if xpath_content:
                        print(f"XPath 内容: {xpath_content}")
                    
                    stats['results'].append({
                        'loop': loop_idx,
                        'query_num': query_num,
                        'query_text': query_text,
                        'success': success,
                        'url': current_url,
                        'xpath_content': xpath_content,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    stats['fail_count'] += 1
                    error_msg = str(e)
                    print(f"❌ 失败: {error_msg}")
                    
                    stats['results'].append({
                        'loop': loop_idx,
                        'query_num': query_num,
                        'query_text': query_text,
                        'success': False,
                        'url': page.url if page else None,
                        'xpath_content': None,
                        'error': error_msg,
                        'timestamp': datetime.now().isoformat()
                    })
                
                # 查询间隔（最后一个查询后不需要等待）
                if query_idx < len(query_list) or loop_idx < loop_count:
                    # sleep(interval)
                    pass
            
            # 每轮循环后的统计
            print(f"\n当前统计: 成功 {stats['success_count']}/{stats['total_queries']}, "
                  f"失败 {stats['fail_count']}/{stats['total_queries']}")
        
        stats['end_time'] = datetime.now()
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        
        # 最终统计
        print(f"\n{'='*60}")
        print("循环查询测试完成")
        print(f"{'='*60}")
        print(f"总查询次数: {stats['total_queries']}")
        print(f"成功次数: {stats['success_count']} ({stats['success_count']/stats['total_queries']*100:.1f}%)")
        print(f"失败次数: {stats['fail_count']} ({stats['fail_count']/stats['total_queries']*100:.1f}%)")
        print(f"总耗时: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
        print(f"平均每次查询: {duration/stats['total_queries']:.1f} 秒")
        print(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"循环查询测试过程中发生错误: {e}", exc_info=True)
        stats['error'] = str(e)
    finally:
        if page:
            pass
            # page.quit()  # 如果需要自动关闭，取消注释
    
    return stats


def main():
    """主程序入口"""
    # 股票列表和查询关键词
    stock_list = ["比亚迪", "中国银行", "中国移动", "吉比特"]
    question_str = [f"{i}散户指标" for i in stock_list]
    
    # 选择模式：'batch' 批量查询，'loop' 循环测试
    mode = 'loop'  # 改为 'batch' 可以执行批量查询
    
    if mode == 'loop':
        # 循环查询测试模式
        print("=" * 60)
        print("i问财循环查询测试")
        print("=" * 60)
        
        # 循环测试参数
        loop_count = 100      # 循环次数
        interval = 2.0       # 每次查询间隔（秒），建议至少2秒
        wait_time = 5        # 每个查询等待页面加载时间（秒）
        
        stats = loop_query_test(
            query_list=question_str,
            loop_count=loop_count,
            interval=interval,
            browser_path=None,      # 使用系统默认路径
            headless=False,         # 显示浏览器窗口
            wait_time=wait_time,
            use_url_param=True
        )
        
        # 保存统计结果到文件（可选）
        # import json
        # with open('query_test_stats.json', 'w', encoding='utf-8') as f:
        #     json.dump(stats, f, ensure_ascii=False, indent=2)
        
    else:
        # 批量查询模式
        print("=" * 60)
        print("i问财批量关键词查询工具")
        print("=" * 60)
        print(f"查询数量: {len(question_str)}")
        print(f"查询列表: {question_str}")
        print("=" * 60)
        print()
        
        results = query_iwencai_batch(
            query_list=question_str,
            browser_path=None,      # 使用系统默认路径
            headless=False,         # 显示浏览器窗口
            wait_time=5,           # 每个查询等待5秒让结果加载
            use_url_param=True,     # 使用 URL 参数直接查询（推荐）
            reuse_browser=True      # 复用浏览器实例，提高效率
        )
        
        # 输出结果汇总
        print("\n" + "=" * 60)
        print("批量查询结果汇总")
        print("=" * 60)
        
        success_count = sum(1 for r in results if r['success'])
        print(f"成功: {success_count}/{len(results)}")
        print()
        
        # 详细输出每个查询结果
        for idx, result in enumerate(results, 1):
            print(f"\n{'='*60}")
            print(f"查询 {idx}: {result['query_text']}")
            print(f"{'='*60}")
            print(f"成功: {result['success']}")
            print(f"页面URL: {result['url']}")
            
            if result['success']:
                print(f"\n结果内容（前1000字符）:")
                print("-" * 60)
                if result['result_text']:
                    print(result['result_text'][:1000])
                    if len(result['result_text']) > 1000:
                        print(f"\n... (总长度: {len(result['result_text'])} 字符，已截断)")
                else:
                    print("(无结果文本)")
                print("-" * 60)
                
                # 显示 XPath 内容（如果存在）
                if 'xpath_content' in result and result['xpath_content']:
                    print(f"\nXPath 提取内容: {result['xpath_content']}")
            else:
                print(f"\n错误信息: {result['error']}")
    
    print("\n" + "=" * 60)
    print("提示: 浏览器窗口将保持打开，您可以手动查看和关闭")
    print("=" * 60)


if __name__ == "__main__":
    main()

