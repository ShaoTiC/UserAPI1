#!/usr/bin/env python3
"""Minimal OpenAI-compatible chat completions mock for local wiring tests."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def build_reply(user_content: str) -> str:
    text = user_content or ""
    if "未提供" in text or "请先向用户索取订单号" in text:
        return (
            "您好，为帮您准确查询物流进度，请提供订单号"
            "（可在「我的订单」中复制）。提供后我再为您核对状态。"
        )
    if "未找到该订单" in text or "不属于当前用户" in text:
        return (
            "您好，未找到该订单的可查询记录。请核对订单号是否正确，"
            "或确认订单属于当前账号；如仍有问题可转人工客服协助。"
        )
    if "物流异常" in text:
        return (
            "您好，当前状态：物流异常。承运商：中通快递，运单号：ZT1122334455。"
            "收件人手机：138****5678；收货地址：浙江省杭州市***。"
            "抱歉，存在异常：派送失败。建议更新收件电话、申请改约派送或催派，也可转人工升级处理。"
        )
    if "超出售后承诺发货时效" in text or ("已付款待发货" in text and "异常原因" in text):
        return (
            "您好，当前状态：已付款待发货。收件人手机：138****5678。"
            "抱歉，超出发货时效，商家尚未揽收。您可以催发货、取消订单，或转人工升级处理/申请赔付指引。"
        )
    if "待付款" in text:
        return (
            "您好，当前状态：待付款。请尽快完成支付；超时未付可能会自动取消。"
            "收件人手机：138****5678。"
        )
    if "已付款待发货" in text:
        return (
            "您好，当前状态：已付款待发货。商家正在备货，暂无运单信息。"
            "请耐心等待商家揽收；如超时未发货可催发货或取消订单。"
            "收件人手机：138****5678。"
        )
    if "已签收" in text:
        return (
            "您好，当前状态：已签收。承运商：圆通速递，运单号：YT555666777。"
            "收件人手机：138****5678。若非本人签收或商品异常，可申请售后；也可对本次服务进行评价。"
        )
    if "已取消" in text:
        return (
            "您好，当前状态：已取消。该订单不会再发货。如仍需商品请重新下单。"
            "收件人手机：138****5678。"
        )
    if "已退款" in text:
        return (
            "您好，当前状态：已退款。退款已完成，款项将原路退回，请留意账单到账情况。"
            "收件人手机：138****5678。"
        )
    if "退货中" in text:
        return (
            "您好，当前状态：退货中。承运商：德邦快递，运单号：DB7788990011。"
            "收件人手机：138****5678。请关注退货进度与退款结果。"
        )
    if "派送中" in text:
        return (
            "您好，当前状态：派送中。承运商：京东物流，运单号：JD9876543210。"
            "收件人手机：138****5678。请保持电话畅通；如需代收可联系快递员。"
        )
    return (
        "您好，当前状态：运输中。承运商：顺丰速运，运单号：SF1234567890。"
        "收件人手机：138****5678；收货地址：浙江省杭州市***。"
        "请持续关注物流详情；签收前请当面核对。"
    )


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode("utf-8") or "{}")
        messages = payload.get("messages") or []
        user = ""
        for msg in messages:
            if msg.get("role") == "user":
                user = str(msg.get("content") or "")
        content = build_reply(user)
        body = {
            "id": "mock-1",
            "object": "chat.completion",
            "model": payload.get("model") or "mock-internal-qwen",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        print("[mock-llm]", fmt % args)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Mock internal LLM listening on http://{args.host}:{args.port}/v1/chat/completions")
    server.serve_forever()


if __name__ == "__main__":
    main()
