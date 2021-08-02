#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/25 9:29 上午
# @File    : jd_joy.py
# @Project : jd_scripts
# @Cron    : 45 8,12,17 * * *
# @Desc    : 京东APP->我的->宠汪汪
import asyncio
import json
import os
import random
import aiohttp
import ujson
from utils.console import println
from urllib.parse import urlencode
from config import USER_AGENT, IMAGES_DIR
from utils.image import save_img, detect_displacement
from utils.browser import open_page, open_browser
from utils.logger import logger
from utils.wraps import jd_init


@jd_init
class JdJoy:
    """
    宠汪汪, 需要使用浏览器方式进行拼图验证。
    """
    # 活动地址
    url = 'https://h5.m.jd.com/babelDiy/Zeus/2wuqXrZrhygTQzYA7VufBEpj4amH/index.html#/pages/jdDog/jdDog'

    headers = {
        "Accept": "application/json,text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-cn",
        "Connection": "keep-alive",
        "Referer": "https://h5.m.jd.com/babelDiy/Zeus/2wuqXrZrhygTQzYA7VufBEpj4amH/index.html",
        "User-Agent": USER_AGENT
    }

    browser = None  # 浏览器对象
    page = None  # 页面标签对象
    
    async def close_browser(self):
        """
        关闭浏览器
        :return:
        """
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            println(e.args)

    @logger.catch
    async def validate(self):
        """
        拼图验证
        :return:
        """
        cookies = [
            {
                'domain': '.jd.com',
                'name': 'pt_pin',
                'value': self.cookies.get('pt_pin'),
            },
            {
                'domain': '.jd.com',
                'name': 'pt_key',
                'value': self.cookies.get('pt_key'),
            }
        ]
        if not self.browser:
            self.browser = await open_browser()
        if not self.page:
            self.page = await open_page(self.browser, self.url, USER_AGENT, cookies)
        page = self.page
        validator_selector = '#app > div > div > div > div.man-machine > div.man-machine-container'
        validator = await page.querySelector(validator_selector)
        if not validator:
            println('{}, 不需要拼图验证...'.format(self.account))
            return True
        else:
            box = await validator.boundingBox()
            if not box:
                println('{}, 不需要拼图验证...'.format(self.account))
                return True

        println('{}, 需要进行拼图验证...'.format(self.account))

        bg_img_selector = '#man-machine-box > div > div.JDJRV-img-panel.JDJRV-embed > div.JDJRV-img-wrap > ' \
                          'div.JDJRV-bigimg > img'

        slider_img_selector = '#man-machine-box > div > div.JDJRV-img-panel.JDJRV-embed > div.JDJRV-img-wrap > ' \
                              'div.JDJRV-smallimg > img'

        for i in range(10):

            println('{}, 正在进行第{}次拼图验证...'.format(self.account, i + 1))
            println('{}, 等待加载拼图验证背景图片...'.format(self.account))
            await page.waitForSelector(bg_img_selector)

            bg_img_ele = await page.querySelector(bg_img_selector)

            println('{}, 等待加载拼图验证滑块图片...'.format(self.account))
            await page.waitForSelector(slider_img_selector)
            slider_img_ele = await page.querySelector(slider_img_selector)

            bg_img_content = await (await bg_img_ele.getProperty('src')).jsonValue()
            slider_img_content = await (await slider_img_ele.getProperty('src')).jsonValue()

            bg_image_path = os.path.join(IMAGES_DIR, 'jd_pet_dog_bg_{}.png'.format(self.account))
            slider_image_path = os.path.join(IMAGES_DIR, 'jd_pet_dog_slider_{}.png'.format(self.account))

            println('{}, 保存拼图验证背景图片:{}!'.format(self.account, bg_image_path))
            save_img(bg_img_content, bg_image_path)

            println('{}, 保存拼图验证滑块图片:{}!'.format(self.account, slider_image_path))
            save_img(slider_img_content, slider_image_path)

            offset = detect_displacement(slider_image_path, bg_image_path)
            println('{}. 拼图偏移量为:{}'.format(self.account, offset))

            slider_btn_selector = '#man-machine-box > div > div.JDJRV-slide-bg > div.JDJRV-slide-inner.JDJRV-slide-btn'
            ele = await page.querySelector(slider_btn_selector)
            box = await ele.boundingBox()
            println('{}, 开始拖动拼图滑块...'.format(self.account))
            await page.hover(slider_btn_selector)
            await page.mouse.down()

            cur_x = box['x']
            cur_y = box['y']
            first = True
            total_delay = 0
            shake_times = 2  # 左右抖动的最大次数

            while offset > 0:
                if first:
                    # 第一次先随机移动偏移量的%60~80%
                    x = int(random.randint(6, 8) / 10 * offset)
                    first = False
                elif total_delay >= 2000:  # 时间大于2s了， 直接拉满
                    x = offset
                else:  # 随机滑动5~30px
                    x = random.randint(5, 30)

                if x > offset:
                    offset = 0
                    x = offset
                else:
                    offset -= x

                cur_x += x

                delay = random.randint(100, 500)
                steps = random.randint(1, 20)
                total_delay += delay
                println('{}, 拼图offset:{}, delay:{}, steps:{}'.format(self.account, cur_x, delay, steps))
                await page.mouse.move(cur_x, cur_y,
                                      {'delay': delay, 'steps': steps})

                if shake_times <= 0:
                    continue

                if total_delay >= 2000:
                    continue

                num = random.randint(1, 10)  # 随机选择是否抖动
                if num % 2 == 1:
                    continue

                shake_times -= 1
                px = random.randint(1, 20)  # 随机选择抖动偏移量
                delay = random.randint(100, 500)
                steps = random.randint(1, 20)
                total_delay += delay
                # 往右拉
                cur_x += px
                println('{}, 拼图向右滑动:offset:{}, delay:{}, steps:{}'.format(self.account, px, delay, steps))
                await page.mouse.move(cur_x, cur_y,
                                      {'delay': delay, 'steps': steps})

                delay = random.randint(100, 500)
                steps = random.randint(1, 20)
                total_delay += delay

                # 往左拉
                cur_x -= px
                println('{}, 拼图向左滑动:offset:{}, delay:{}, steps:{}'.format(self.account, px, delay, steps))
                await page.mouse.move(cur_x, cur_y,
                                      {'delay': delay, 'steps': steps})
            println('{}, 第{}次拼图验证, 耗时:{}s.'.format(self.account, i + 1, total_delay / 1000))
            await page.mouse.up()
            await asyncio.sleep(3)
            println('{}, 正在获取验证结果, 等待3s...'.format(self.account))
            slider_img_ele = await page.querySelector(slider_img_selector)
            if slider_img_ele is None:
                println('{}, 第{}次拼图验证, 验证成功!'.format(self.account, i + 1))
                break
            else:
                println('{}, 第{}次拼图验证, 验证失败, 继续验证!'.format(self.account, i + 1))

        validator = await page.querySelector(validator_selector)
        if not validator:
            println('{}, 已完成拼图验证...'.format(self.account))
            return True
        else:
            box = await validator.boundingBox()
            if not box:
                println('{}, 已完成拼图验证...'.format(self.account))
                return True
            else:
                println('{}, 无法完成拼图验证...'.format(self.account))
                return None

    async def request(self, session, path, body=None, method='GET', post_type='json'):
        """
        请求数据
        :param session:
        :param method:
        :param path:
        :param post_type:
        :param body:
        :return:
        """
        try:
            default_params = {
                'reqSource': 'h5',
                'invokeKey': 'qRKHmL4sna8ZOP9F'
            }
            if method == 'GET' and body:
                default_params.update(body)

            url = 'https://jdjoy.jd.com/common/{}'.format(path) + '?' + urlencode(default_params)

            if method == 'GET':
                response = await session.get(url)
            else:
                if post_type == 'json':
                    content_type = session.headers.get('Content-Type', None)
                    if content_type:
                        session.headers.pop('Content-Type')
                    response = await session.post(url, json=body)
                else:
                    session.headers.add('Content-Type', 'application/x-www-form-urlencoded')
                    response = await session.post(url, data=body)

            text = await response.text()
            data = json.loads(text)
            if not data['errorCode']:
                if 'data' in data:
                    return data['data']
                elif 'datas' in data:
                    return data['datas']
                return data

            if data['errorCode'] == 'H0001':  # 需要拼图验证
                println('{}, 需要进行拼图验证!'.format(self.account))
                is_success = await self.validate()
                if is_success:
                    return await self.request(session, path, body, method)
            return data

        except Exception as e:
            println('{}, 获取服务器数据失败:{}'.format(self.account, e.args))
            return {
                'errorCode': 9999
            }

    async def sign_every_day(self, session, task):
        """
        每日签到
        """
        println('{}, 签到功能暂时未完成!'.format(self.account))

    @logger.catch
    async def get_award(self, session, task):
        """
        领取任务奖励狗粮
        """
        path = 'pet/getFood'
        body = {
            'taskType': task['taskType']
        }
        data = await self.request(session, path, body)

        if not data or (data['errorCode'] and 'fail' in data['errorCode']):
            println('{}, 领取任务: 《{}》 奖励失败!'.format(self.account, task['taskName']))
        else:
            println('{}, 成功领取任务: 《{}》 奖励!'.format(self.account, task['taskName']))

    @logger.catch
    async def scan_market(self, session, task):
        """
        逛会场
        """
        market_list = task['scanMarketList']
        path = 'pet/scan'
        for market in market_list:
            market_link = market['marketLink']
            if market_link == '':
                market_link = market['marketLinkH5']
            params = {
                'marketLink': market_link,
                'taskType': task['taskType']
            }
            data = await self.request(session, path, params, method='POST')
            if not data or (data['errorCode'] and 'success' not in data['errorCode']):
                println('{}, 无法完成逛会场任务:{}!'.format(self.account, market['marketName']))
            else:
                println('{}, 成功完成逛会场任务:{}!'.format(self.account, market['marketName']))
            await asyncio.sleep(3)

    @logger.catch
    async def follow_shop(self, session, task):
        """
        关注店铺
        """
        click_path = 'pet/icon/click'
        shop_list = task['followShops']
        for shop in shop_list:
            click_params = {
                'iconCode': 'follow_shop',
                'linkAddr': shop['shopId']
            }
            await self.request(session, click_path, click_params)
            await asyncio.sleep(0.5)

            follow_path = 'pet/followShop'
            follow_params = {
                'shopId': shop['shopId']
            }
            data = await self.request(session, follow_path, follow_params, post_type='body', method='POST')
            if not data or 'success' not in data:
                println('{}, 无法关注店铺{}'.format(self.account, shop['name']))
            else:
                println('{}, 成功关注店铺: {}'.format(self.account, shop['name']))
            await asyncio.sleep(1)

    @logger.catch
    async def follow_good(self, session, task):
        """
        关注商品
        """
        path = 'pet/icon/click'
        good_list = task['followGoodList']

        for good in good_list:
            params = {
                'iconCode': 'follow_good',
                'linkAddr': good['sku']
            }
            await self.request(session, path, params)
            await asyncio.sleep(1)

            follow_path = 'pet/followGood'
            params = {
                'sku': good['sku']
            }
            data = await self.request(session, follow_path, params, method='POST', post_type='form')
            if not data:
                println('{}, 关注商品:{}失败!'.format(self.account, good['skuName']))
            else:
                println('{}, 成功关注商品:{}!'.format(self.account, good['skuName']))

    @logger.catch
    async def follow_channel(self, session, task):
        """
        """
        channel_path = 'pet/getFollowChannels'
        channel_list = await self.request(session, channel_path)
        if not channel_list:
            println('{}, 获取频道列表失败!'.format(self.account))
            return

        for channel in channel_list:
            if channel['status']:
                continue
            click_path = 'pet/icon/click'
            click_params = {
                'iconCode': 'follow_channel',
                'linkAddr': channel['channelId']
            }
            await self.request(session, click_path, click_params)
            follow_path = 'pet/scan'
            follow_params = {
                'channelId': channel['channelId'],
                'taskType': task['taskType']
            }
            data = await self.request(session, follow_path, follow_params, method='POST')
            await asyncio.sleep(0.5)
            if not data or (
                    data['errorCode'] and 'success' not in data['errorCode'] and 'repeat' not in data['errorCode']):
                println('{}, 关注频道:{}失败!'.format(self.account, channel['channelName']))
            else:
                println('{}, 成功关注频道:{}!'.format(self.account, channel['channelName']))
            await asyncio.sleep(3.1)

    @logger.catch
    async def do_task(self, session):
        """
        做任务
        :return:
        """
        path = 'pet/getPetTaskConfig'
        task_list = await self.request(session, path)
        if not task_list:
            println('{}, 获取任务列表失败!'.format(self.account))
            return

        for task in task_list:
            if task['receiveStatus'] == 'unreceive':
                await self.get_award(session, task)
                await asyncio.sleep(1)

            if task['joinedCount'] and task['joinedCount'] >= task['taskChance']:
                println('{}, 任务:{}今日已完成!'.format(self.account, task['taskName']))
                continue

            if task['taskType'] == 'SignEveryDay':
                await self.sign_every_day(session, task)

            elif task['taskType'] == 'FollowGood':  # 关注商品
                await self.follow_good(session, task)

            elif task['taskType'] == 'FollowChannel':  # 关注频道
                await self.follow_channel(session, task)

            elif task['taskType'] == 'FollowShop':  # 关注店铺
                await self.follow_shop(session, task)

            elif task['taskType'] == 'ScanMarket':  # 逛会场
                await self.scan_market(session, task)

    @logger.catch
    async def get_friend_list(self, session, page=1):
        """
        获取好友列表
        """
        path = 'pet/h5/getFriends'
        params = {
            'itemsPerPage': 20,
            'currentPage': page
        }
        friend_list = await self.request(session, path, params)
        if not friend_list:
            return []
        return friend_list

    @logger.catch
    async def help_friend_feed(self, session):
        """
        帮好友喂狗
        """
        cur_page = 0
        while True:
            cur_page += 1
            friend_list = await self.get_friend_list(session, page=cur_page)
            if not friend_list:
                break

            for friend in friend_list:
                if friend['status'] == 'chance_full':
                    println('{}, 今日帮好友喂狗次数已用完成!'.format(self.account))
                    return

                if friend['status'] != 'not_feed':
                    continue

                feed_path = 'pet/helpFeed'
                feed_params = {
                    'friendPin': friend['friendPin']
                }
                data = await self.request(session, feed_path, feed_params)
                if data and data['errorCode'] and 'ok' in data['errorCode']:
                    println('{}, 成功帮好友:{} 喂狗!'.format(self.account, friend['friendName']))
                else:
                    println('{}, 无法帮好友:{}喂狗!'.format(self.account, friend['friendName']))
                    error_code = data.get('errorCode', '')
                    if 'full' in error_code:
                        break
                await asyncio.sleep(1)
            await asyncio.sleep(1)

    @logger.catch
    async def joy_race(self, session, level=2):
        """
        参与赛跑
        """
        click_path = 'pet/icon/click'
        click_params = {
            'iconCode': 'race_match',
        }
        await self.request(session, click_path, click_params)
        await asyncio.sleep(0.5)

        match_path = 'pet/combat/match'
        match_params = {
            'teamLevel': level
        }

        for i in range(10):
            data = await self.request(session, match_path, match_params)
            if data['petRaceResult'] == 'participate':
                println('{}, 成功参与赛跑!'.format(self.account))
                return
            await asyncio.sleep(1)
        println('{}, 无法参与赛跑!'.format(self.account))

    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies,
                                         json_serialize=ujson.dumps) as session:
            await self.joy_race(session)
            await self.help_friend_feed(session)
            await self.do_task(session)

        await self.close_browser()


if __name__ == '__main__':
    from utils.process import process_start
    from config import JOY_PROCESS_NUM
    process_start(JdJoy, '宠汪汪做任务', process_num=JOY_PROCESS_NUM)
