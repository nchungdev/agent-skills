#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Expense Engine for Categorization, Aggregation & Analytics
- Phân loại danh mục thông minh theo từ khóa (category_rules.json)
- Gom nhóm theo Tháng & Xử lý các giao dịch Chưa xác định ngày
- Tính toán tổng tiền, tỷ trọng %, phát hiện giao dịch trùng lặp
"""

import os
import json
import re
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_FILE = os.path.join(SCRIPT_DIR, "category_rules.json")

def load_category_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("categories", {})
    return {}

def categorize_transaction(transaction, categories_rule):
    """Xác định danh mục chi tiêu dựa trên thông tin merchant và mặt hàng."""
    search_text = " ".join([
        transaction.get("merchant", ""),
        transaction.get("items_summary", ""),
        " ".join(transaction.get("items_list", [])),
        transaction.get("order_id", "")
    ]).lower()

    for cat_name, cat_data in categories_rule.items():
        if cat_name == "Uncategorized":
            continue
        keywords = cat_data.get("keywords", [])
        for kw in keywords:
            # So khớp từ khóa nguyên từ hoặc cụm từ
            if re.search(r'\b' + re.escape(kw.lower()) + r'\b', search_text, re.IGNORECASE) or kw.lower() in search_text:
                return cat_name, cat_data.get("name_vi", cat_name), cat_data.get("icon", "🏷️")

    return "Uncategorized", "Chưa phân loại / Khác", "❓"

def detect_duplicates(transactions):
    """Phát hiện các giao dịch nghi ngờ trùng lặp (ví dụ vừa đồng bộ Shopee vừa có ảnh bill)."""
    seen = {}
    duplicates = []
    
    for tx in transactions:
        amt = tx.get("amount", 0)
        date_short = (tx.get("date") or "")[:10]
        # Khóa so khớp: Số tiền + Ngày (nếu có)
        if amt > 0 and date_short and date_short != "Unspecifie":
            key = f"{amt}_{date_short}"
            if key in seen:
                prev_tx = seen[key]
                # Nếu 1 từ shopee/tiktok và 1 từ image thì khả năng cao là trùng
                if prev_tx.get("source") != tx.get("source"):
                    duplicates.append({
                        "original_id": prev_tx.get("id"),
                        "duplicate_id": tx.get("id"),
                        "amount": amt,
                        "date": date_short,
                        "reason": f"Trùng khớp số tiền {amt:,.0f} VND vào ngày {date_short} giữa {prev_tx.get('source')} và {tx.get('source')}"
                    })
            else:
                seen[key] = tx
    return duplicates

def aggregate_expenses(transactions):
    """Gom nhóm chi tiêu theo Tháng và theo Danh mục."""
    categories_rule = load_category_rules()
    
    # 1. Gán danh mục cho từng giao dịch
    for tx in transactions:
        cat_key, cat_vi, cat_icon = categorize_transaction(tx, categories_rule)
        tx["category_key"] = cat_key
        tx["category_name"] = cat_vi
        tx["category_icon"] = cat_icon

    # 2. Phát hiện trùng lặp
    duplicates = detect_duplicates(transactions)

    # 3. Gom nhóm theo tháng
    monthly_data = defaultdict(lambda: {
        "month": "",
        "total_amount": 0.0,
        "transaction_count": 0,
        "categories": defaultdict(lambda: {"amount": 0.0, "count": 0, "name_vi": "", "icon": ""}),
        "sources": defaultdict(lambda: {"amount": 0.0, "count": 0}),
        "transactions": []
    })

    grand_total = 0.0
    for tx in transactions:
        month = tx.get("month") or "Unspecified"
        amt = tx.get("amount", 0.0)
        cat_key = tx.get("category_key")
        source = tx.get("source", "other")

        monthly_data[month]["month"] = month
        monthly_data[month]["total_amount"] += amt
        monthly_data[month]["transaction_count"] += 1
        
        # Category breakdown
        monthly_data[month]["categories"][cat_key]["amount"] += amt
        monthly_data[month]["categories"][cat_key]["count"] += 1
        monthly_data[month]["categories"][cat_key]["name_vi"] = tx.get("category_name")
        monthly_data[month]["categories"][cat_key]["icon"] = tx.get("category_icon")

        # Source breakdown
        monthly_data[month]["sources"][source]["amount"] += amt
        monthly_data[month]["sources"][source]["count"] += 1

        monthly_data[month]["transactions"].append(tx)
        grand_total += amt

    # 4. Tính toán phần trăm tỷ trọng
    result_months = {}
    for month, data in sorted(monthly_data.items(), key=lambda x: x[0], reverse=True):
        m_total = data["total_amount"]
        cat_list = []
        for c_key, c_val in data["categories"].items():
            pct = (c_val["amount"] / m_total * 100.0) if m_total > 0 else 0.0
            cat_list.append({
                "category_key": c_key,
                "name_vi": c_val["name_vi"],
                "icon": c_val["icon"],
                "amount": c_val["amount"],
                "count": c_val["count"],
                "percentage": round(pct, 1)
            })
        
        # Sắp xếp danh mục theo số tiền giảm dần
        cat_list.sort(key=lambda x: x["amount"], reverse=True)

        # Source percentages
        source_list = []
        for s_key, s_val in data["sources"].items():
            s_pct = (s_val["amount"] / m_total * 100.0) if m_total > 0 else 0.0
            source_list.append({
                "source": s_key,
                "amount": s_val["amount"],
                "count": s_val["count"],
                "percentage": round(s_pct, 1)
            })

        result_months[month] = {
            "month": month,
            "total_amount": m_total,
            "transaction_count": data["transaction_count"],
            "categories": cat_list,
            "sources": source_list,
            "transactions": sorted(data["transactions"], key=lambda x: x.get("date", ""), reverse=True)
        }

    return {
        "grand_total": grand_total,
        "total_transactions": len(transactions),
        "months": result_months,
        "duplicates": duplicates
    }
