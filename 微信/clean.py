#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wechat2firefly.py
微信账单 → Firefly III 12列标准CSV
python wechat2firefly.py 微信支付账单.xlsx
"""
import pandas as pd
import sys, os, re

# ---------- 配置 ----------
DROP_STATUS = {"已退款", "已全额退款", "退款成功"}   # 微信退款描述
DROP_TYPE   = {"/"}                                 # 中性交易
AMOUNT_SIGN = {"支出": 1, "收入": -1, "/": 0}      # 微信的收/支值
ACCOUNT_MAP = {                                     # 微信支付方式 → Firefly 账户名
    "零钱": "微信零钱",
    "零钱通": "微信零钱通",
    "招商银行储蓄卡(7699)": "招商银行储蓄卡(7699)",
    "农业银行储蓄卡(4976)": "农业银行储蓄卡(4976)",
    "": "微信零钱",
}
# ---------------------------


def clean_wechat(xlsx_file: str, output_csv: str = None):
    if output_csv is None:
        base, _ = os.path.splitext(xlsx_file)
        output_csv = f"{base}_clean.csv"

    # 1. 读微信账单（从第 1 个 sheet 跳过表头）
    df = pd.read_excel(xlsx_file, sheet_name=0, dtype=str, skiprows=16)

    # 2. 统一列名（去掉括号）
    df.columns = [re.sub(r'[（()）]', '', c) for c in df.columns]
    df = df.rename(columns={
        "交易时间": "交易时间",
        "收/支": "收/支",
        "金额元": "金额",
        "支付方式": "支付方式",
        "当前状态": "交易状态",
        "交易单号": "交易订单号",
        "交易对方": "交易对方",
        "商品": "商品说明",
    })

    # 3. 过滤无用行
    df = df[~df["交易状态"].str.contains("|".join(DROP_STATUS), na=False)]
    df = df[~df["收/支"].isin(DROP_TYPE)]

    # 4. 金额去符号并带方向
    df["金额"] = df["金额"].str.replace("¥", "").astype(float)
    sign = df["收/支"].map(AMOUNT_SIGN)
    df["amount_negated"] = sign * df["金额"]

    # 5. 账户映射
    df["account-name"] = df["支付方式"].map(ACCOUNT_MAP).fillna("微信零钱")

    # 6. 组装 12 列（与 Firefly config 顺序一致）
    out = pd.DataFrame()
    out["date_transaction"]   = pd.to_datetime(df["交易时间"]).dt.strftime("%Y/%m/%d %H:%M")
    out["category-name"]      = df["收/支"]  # 或 df["交易类型"]
    out["opposing-name"]      = df["交易对方"]
    out["description"]        = df["商品说明"]
    out["amount_negated"]     = df["amount_negated"]
    out["account-name"]       = df["account-name"]
    out["internal_reference"] = df["交易订单号"].str.strip()

    # 7. 补 5 个空列 → 12 列
    for i in range(1, 6):
        out[f"_ignore{i}"] = ""
    cols = ["date_transaction","category-name","opposing-name","_ignore1",
            "description","_ignore2","amount_negated","account-name",
            "_ignore3","internal_reference","_ignore4","_ignore5"]
    out = out[cols]

    # 8. 导出
    out.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"✅ 微信 12 列标准CSV已生成 → {output_csv}")
    return output_csv


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python wechat2firefly.py <微信账单.xlsx> [输出.csv]")
        sys.exit(1)
    infile = sys.argv[1]
    outfile = sys.argv[2] if len(sys.argv) > 2 else None
    clean_wechat(infile, outfile)