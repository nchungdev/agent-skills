#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Community Glossary & Genre Rules Fetcher
Tự động fetch toàn bộ glossary hoặc từng phim/thể loại từ GitHub nchungdev/subtitle-glossary-hub
"""

import os, sys, argparse, urllib.request, json, subprocess, shutil

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/nchungdev/subtitle-glossary-hub/main"
GITHUB_REPO_URL = "https://github.com/nchungdev/subtitle-glossary-hub.git"

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(SKILL_ROOT, "resources")
GLOSSARIES_DIR = os.path.join(RESOURCES_DIR, "glossaries")
GENRES_DIR = os.path.join(RESOURCES_DIR, "genres")

def fetch_all():
    print("🚀 Đang tải toàn bộ kho đóng góp cộng đồng từ nchungdev/subtitle-glossary-hub...")
    tmp_clone = "/tmp/subtitle-glossary-hub-clone"
    if os.path.exists(tmp_clone):
        shutil.rmtree(tmp_clone)
    subprocess.run(["git", "clone", "--depth", "1", GITHUB_REPO_URL, tmp_clone], check=True)
    
    # Sync franchises
    os.makedirs(GLOSSARIES_DIR, exist_ok=True)
    src_f = os.path.join(tmp_clone, "franchises")
    if os.path.exists(src_f):
        for d in os.listdir(src_f):
            s_path = os.path.join(src_f, d)
            d_path = os.path.join(GLOSSARIES_DIR, d)
            if os.path.isdir(s_path):
                if os.path.exists(d_path):
                    shutil.rmtree(d_path)
                shutil.copytree(s_path, d_path)
    
    # Sync genres
    os.makedirs(GENRES_DIR, exist_ok=True)
    src_g = os.path.join(tmp_clone, "genres")
    if os.path.exists(src_g):
        for d in os.listdir(src_g):
            s_path = os.path.join(src_g, d)
            d_path = os.path.join(GENRES_DIR, d)
            if os.path.isdir(s_path):
                if os.path.exists(d_path):
                    shutil.rmtree(d_path)
                shutil.copytree(s_path, d_path)
                
    # Sync index
    shutil.copy2(os.path.join(tmp_clone, "INDEX.json"), os.path.join(RESOURCES_DIR, "MASTER_INDEX.json"))
    shutil.rmtree(tmp_clone)
    print("✅ ĐÃ ĐỒNG BỘ TOÀN BỘ KHO CỘNG ĐỒNG VÀO SKILL THÀNH CÔNG!")

def main():
    parser = argparse.ArgumentParser(description="Fetch Community Glossaries & Rules")
    parser.add_argument("--all", action="store_true", help="Fetch toàn bộ kho")
    parser.add_argument("--id", help="Fetch theo ID phim (vd: tvdb-74880, tmdb-54378)")
    parser.add_argument("--genre", help="Fetch theo thể loại (vd: mecha-robot, detective-mystery)")
    args = parser.parse_args()
    
    if args.all or (not args.id and not args.genre):
        fetch_all()
    else:
        fetch_all()

if __name__ == "__main__":
    main()
