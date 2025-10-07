#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alipay2firefly.py
清洗支付宝账单 → Firefly III 12列标准CSV
python alipay2firefly.py 支付宝交易明细.csv
"""
import pandas as pd
import sys
import os

# ---------- 配置 ----------
AMOUNT_SIGN = {"支出": 1, "收入": -1, "不计收支": 0}
ACCOUNT_MAP = {
    "余额宝": "余额宝",
    "余额宝&碰一下立减": "余额宝",
    "工商银行储蓄卡(3445)": "工商银行储蓄卡(3445)",
    "工商银行储蓄卡(3445)&余额宝": "工商银行储蓄卡(3445)",
    "工商银行储蓄卡(3445)&碰一下立减": "工商银行储蓄卡(3445)",
    "招商银行储蓄卡(7699)": "招商银行储蓄卡(7699)",
    "农业银行储蓄卡(4976)": "农业银行储蓄卡(4976)",
    "账户余额": "余额宝",
    "": "余额宝",
}
DROP_STATUS = {"交易关闭", "退款成功"}
DROP_TYPE  = {"不计收支"}
# ---------------------------


def clean_alipay(input_csv: str, output_csv: str = None):
    if output_csv is None:
        base, _ = os.path.splitext(input_csv)
        output_csv = f"{base}_clean.csv"

    # 读取
    df = pd.read_csv(input_csv, dtype=str, skiprows=24)

    # 过滤
    df = df[~df["交易状态"].isin(DROP_STATUS)]
    df = df[~df["收/支"].isin(DROP_TYPE)]

    # 金额
    df["金额"] = pd.to_numeric(df["金额"], errors="coerce")
    df["amount_negated"] = df["收/支"].map(AMOUNT_SIGN) * df["金额"]

    # 账户映射
    df["account-name"] = df["收/付款方式"].map(ACCOUNT_MAP).fillna("余额宝")

    # 组装7个有用列
    out = pd.DataFrame()
    out["date_transaction"]   = pd.to_datetime(df["交易时间"]).dt.strftime("%Y/%m/%d %H:%M")
    out["category-name"]      = df["交易分类"]
    out["opposing-name"]      = df["交易对方"]
    out["description"]        = df["商品说明"]
    out["amount_negated"]     = df["amount_negated"]
    out["account-name"]       = df["account-name"]
    out["internal_reference"] = df["交易订单号"].str.strip()

    # 补5个空列，凑够12列（与config roles顺序一致）
    cols_final = [
        "date_transaction",   # 0
        "category-name",      # 1
        "opposing-name",      # 2
        "_ignore1",           # 3  (原roles[3])
        "description",        # 4
        "_ignore2",           # 5  (原roles[5])
        "amount_negated",     # 6
        "account-name",       # 7
        "_ignore3",           # 8  (原roles[8])
        "internal_reference", # 9
        "_ignore4",           # 10 (原roles[10])
        "_ignore5",           # 11 (原roles[11])
    ]
    for col in ["_ignore1", "_ignore2", "_ignore3", "_ignore4", "_ignore5"]:
        out[col] = ""
    out = out[cols_final]

    # 导出
    out.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"✅ 12列标准CSV已生成 -> {output_csv}")
    return output_csv


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python alipay2firefly.py <支付宝csv> [输出csv]")
        sys.exit(1)
    infile = sys.argv[1]
    outfile = sys.argv[2] if len(sys.argv) > 2 else None
    clean_alipay(infile, outfile)