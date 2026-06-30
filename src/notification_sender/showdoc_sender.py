# -*- coding: utf-8 -*-
"""
ShowDoc 推送服务

职责：
1. 通过 ShowDoc Push API 发送微信推送消息

ShowDoc 推送平台：https://push.showdoc.com.cn
协议：POST https://push.showdoc.com.cn/api/push/{token}
      Body: {"title": "标题", "content": "内容"}
"""
import logging
from typing import Optional
from datetime import datetime
import requests

from src.config import Config

logger = logging.getLogger(__name__)


class ShowdocSender:
    """
    ShowDoc 推送发送器

    通过 ShowDoc 平台的 Push API 推送消息到绑定的微信。
    用户扫码绑定后获得 token，即可免费推送。
    """

    API_BASE_URL = "https://push.showdoc.com.cn/server/api/push"

    def __init__(self, config: Config):
        """
        初始化 ShowDoc 配置

        Args:
            config: 配置对象
        """
        self._showdoc_token = getattr(config, 'showdoc_token', None)

    @property
    def is_configured(self) -> bool:
        """检查是否已配置 ShowDoc Token"""
        return bool(self._showdoc_token and self._showdoc_token.strip())

    def send_to_showdoc(
        self,
        content: str,
        title: Optional[str] = None,
        *,
        timeout_seconds: Optional[float] = None,
    ) -> bool:
        """
        推送消息到 ShowDoc

        Args:
            content: 消息内容（Markdown 格式）
            title: 消息标题（可选，留空自动生成日期标题）

        Returns:
            是否发送成功
        """
        if not self.is_configured:
            logger.warning("ShowDoc Token 未配置，跳过推送")
            return False

        api_url = f"{self.API_BASE_URL}/{self._showdoc_token.strip()}"

        if title is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
            title = f"📈 股票分析报告 - {date_str}"

        try:
            payload = {
                "title": title,
                "content": content,
            }

            response = requests.post(
                api_url,
                json=payload,
                timeout=timeout_seconds or 15,
            )

            if response.status_code == 200:
                try:
                    result = response.json()
                    # ShowDoc API 成功时 error_code=0
                    error_code = result.get('error_code') if isinstance(result, dict) else None
                    if error_code is None or error_code == 0:
                        logger.info("ShowDoc 消息发送成功")
                        return True
                    error_msg = result.get('error_message', '未知错误')
                    logger.error(f"ShowDoc 返回错误 (error_code={error_code}): {error_msg}")
                    return False
                except (ValueError, AttributeError):
                    # 非 JSON 响应但 HTTP 200，视为成功
                    logger.info("ShowDoc 消息发送成功（非 JSON 响应）")
                    return True

            logger.error(
                f"ShowDoc 请求失败: HTTP {response.status_code}, "
                f"body={str(response.text)[:200]}"
            )
            return False

        except requests.exceptions.Timeout:
            logger.error("ShowDoc 请求超时")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"ShowDoc 连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"发送 ShowDoc 消息失败: {e}")
            return False
