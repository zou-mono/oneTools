# -*- coding: utf-8 -*-

from UICore.log4p import Log
import aiohttp
import asyncio
import json

HTTP_STATUS_CODES_TO_RETRY = [500, 502, 503, 504]
log = Log(__name__)

class FailedRequest(Exception):
    """
    A wrapper of all possible exception during a HTTP request
    """
    code = 0
    message = ''
    url = ''
    raised = ''

    def __init__(self, *, raised='', message='', code='', url=''):
        self.raised = raised
        self.message = message
        self.code = code
        self.url = url

        super().__init__("code:{c} url={u} message={m} raised={r}".format(
            c=self.code, u=self.url, m=self.message, r=self.raised))


async def send_http(session, method, url, *,
                    retries=1,
                    respond_Type='content',
                    interval=1,
                    backoff=1,
                    read_timeout=30,
                    http_status_codes_to_retry=HTTP_STATUS_CODES_TO_RETRY,
                    **kwargs):
    """
    Sends a HTTP request and implements a retry logic.

    Arguments:
        session (obj): A client aiohttp session object
        method (str): Method to use
        url (str): URL for the request
        retries (int): Number of times to retry in case of failure
        interval (float): Time to wait before retries
        backoff (int): Multiply interval by this factor after each failure
        read_timeout (float): Time to wait for a response
    """
    backoff_interval = interval
    raised_exc = None
    attempt = 0

    if method not in ['get', 'patch', 'post']:
        raise ValueError

    if respond_Type not in ['content', 'text', 'json']:
        raise ValueError

    if retries == -1:  # -1 means retry indefinitely
        attempt = -1
    elif retries == 0:  # Zero means don't retry
        attempt = 1
    else:  # any other value means retry N times
        attempt = retries + 1

    while attempt != 0:
        if raised_exc:
            log.error('传输 {} method:{}, url:{}, 剩余重试次数为 {}, '
                      '暂停 {}秒'.format(raised_exc, method.upper(), url,
                      attempt, backoff_interval))
            await asyncio.sleep(backoff_interval)
            # bump interval for the next possible attempt
            backoff_interval = backoff_interval * backoff
        # log.info('向服务器发送{} {}, 参数为{}'.format(method.upper(), url, kwargs))
        try:
            # with aiohttp.ClientTimeout(total=read_timeout) as timeout:
            timeout = aiohttp.ClientTimeout(total=read_timeout)
            async with getattr(session, method)(url, timeout=timeout, **kwargs) as response:
                if response.status == 200:
                    # try:
                    if respond_Type == 'content':
                        data = await response.read()
                    elif respond_Type == 'json':
                        data = await response.json()
                    elif respond_Type == 'text':
                        data = await response.text()
                    raised_exc = None
                    return data, response.status

                elif response.status in http_status_codes_to_retry:
                    raise Exception(
                        'received invalid response code:{} url:{} error:{}'
                        ' response:{}'.format(response.status, url, '',
                        response.reason)
                    )
                    # raised_exc = FailedRequest(code=response.status, message=response.reason, url=url,
                    #                            raised='')
                    # raise aiohttp.ClientError
                    # raise aiohttp.errors.HttpProcessingError(
                    #     code=response.status, message=response.reason)
                elif response.status == 404:
                    raised_exc = None
                    # log.warning('received empty data for {}.'.format(url))
                    return None, response.status
                else:
                    try:
                        if respond_Type == 'content':
                            data = await response.read()
                        elif respond_Type == 'json':
                            data = await response.json()
                        elif respond_Type == 'text':
                            data = await response.text()
                    except json.decoder.JSONDecodeError as exc:
                        log.error(
                            'failed to decode response code:%s url:{} '
                            'error:{} response:{}', response.status, url,
                            exc)
                        raise FailedRequest(
                            code=response.status, message=exc,
                            raised=exc.__class__.__name__, url=url)
                    else:
                        raise Exception('received {} for {}'.format(data, url))
                        # print(data['errors'][0]['detail'])
                        raised_exc = None
                response.close()
                return None, response.status
        except aiohttp.ClientError as exc:
            try:
                code = exc.status
            except AttributeError:
                code = ''
            raise Exception('code:{} url={} raised={}'.format(code, url, exc.__class__.__name__))
            # log.debug('code:{} url={} message={} raised={}'.format(code, url, exc, exc.__class__.__name__))
            # raised_exc = FailedRequest(code=code, message=exc, url=url,
            #                            raised=exc.__class__.__name__)
        else:
            raised_exc = None
            break

        attempt -= 1
        # if attempt > 0:
        #     log.warning('HTTP请求失败! 尝试重新发送... method:{} url:{} '.format(method.upper(), url))

    if raised_exc:
        raise raised_exc
