#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared working-directory resolution for the media skills.

Plugins are installed independently and cannot import each other, so this small
reader is copied into each one. media-hub owns the schema — see
media-hub/skills/media-hub/scripts/core/settings.py — and this file must stay
compatible with it.

Root precedence:
  1. MEDIA_HUB_HOME                                explicit, per-run override
  2. a .mediahub found above the current directory project-local wins
  3. media_hub_home in the settings file           pinned fallback
  4. <cwd>/.mediahub                               created on first use

A pinned setting must not beat a project-local .mediahub, or working inside a
project would still write to whatever root was configured globally.

The hub root is project-local and hidden: a ".media-hub" directory located by walking
up from the current directory, the way git locates ".git". Running from
/Volumes/512GB/AI Workspace keeps everything in
/Volumes/512GB/AI Workspace/.media-hub.

    <root>/<Collection>/Movies/<Title (Year) {tmdb-id}>/    video + subs + nfo + art
    <root>/<Collection>/TV Shows/<Title (Year) {tvdb-id}>/  same, with Season NN/
    <root>/.staging/   raw downloads before they are organised into a title folder
    <root>/.cache/  .logs/  .media_hub.db

Collection first, then type: a franchise with both a series and films keeps them
together (Black Jack has one TV universe and two movies). One folder per title holds
everything for that title, so subtitles are edited beside the episodes they belong to
and the title folder is the unit that gets synced.

Note this is deliberately NOT a Plex scan root: Plex libraries are typed, so point it
at the Movies/ and TV Shows/ folders, or sync into a typed library.
"""

import os
import re
import json
from pathlib import Path

GLOBAL_SETTINGS = Path.home() / ".gemini" / "config" / "media_hub_settings.json"
CONFIG_BASENAME = "config.json"
HUB_DIRNAME = ".media-hub"

_ENV = {
    "media_hub_home": "MEDIA_HUB_HOME",
    "staging_dir": "MEDIA_HUB_STAGING_DIR",
    "logs_dir": "MEDIA_HUB_LOGS_DIR",
}


def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _settings(root=None):
    """Global settings, with the project's own config.json layered on top."""
    cfg = _read(GLOBAL_SETTINGS)
    if root:
        cfg.update(_read(Path(root) / CONFIG_BASENAME))
    return cfg


def find_hub_root(start=None):
    """Nearest existing .mediahub directory, walking up from `start` like git."""
    try:
        cur = Path(start or os.getcwd()).resolve()
    except Exception:
        return None
    for candidate in [cur, *cur.parents]:
        hub = candidate / HUB_DIRNAME
        if hub.is_dir():
            return str(hub)
    return None


def hub_dirs(create=False):
    """Absolute paths for every directory a skill may write to."""
    # Resolve the root from env/discovery first — it must not depend on a config file
    # that lives inside the root.
    cfg = _settings()
    for key, env in _ENV.items():
        if os.environ.get(env):
            cfg[key] = os.environ[env]

    env_home = os.environ.get("MEDIA_HUB_HOME")
    home = (os.path.expanduser(env_home) if env_home
            else find_hub_root()
            or (os.path.expanduser(cfg["media_hub_home"]) if cfg.get("media_hub_home") else None)
            or os.path.join(os.getcwd(), HUB_DIRNAME))

    cfg = _settings(home)          # re-read with the project config layered on
    for key, env in _ENV.items():
        if os.environ.get(env):
            cfg[key] = os.environ[env]

    def under(value, name):
        return os.path.expanduser(value) if value else os.path.join(home, name)

    dirs = {
        "media_hub_home": home,
        "movies_dirname": cfg.get("movies_dirname") or "Movies",
        "tv_dirname": cfg.get("tv_dirname") or "TV Shows",
        "staging_dir": under(cfg.get("staging_dir"), ".staging"),
        "logs_dir": under(cfg.get("logs_dir"), ".logs"),
        "cache_dir": under(cfg.get("cache_dir"), ".cache"),
    }
    if create:
        for path in dirs.values():
            try:
                Path(path).mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        # The root is hidden but git would still track it, so make it ignore itself
        # wherever it lands inside a repository.
        try:
            keep = Path(home) / ".gitignore"
            if not keep.exists():
                keep.parent.mkdir(parents=True, exist_ok=True)
                keep.write_text("*\n", encoding="utf-8")
        except Exception:
            pass
    return dirs


def staging_dir(create=True):
    return hub_dirs(create=create)["staging_dir"]


def safe_title(title):
    return re.sub(r"[\x00-\x1f/\\]+", "_", str(title or "").strip()).strip(". ")[:150] or "untitled"


def collection_dir(collection, create=True):
    """<root>/<Collection>/ — everything belonging to one franchise."""
    d = Path(hub_dirs(create=create)["media_hub_home"]) / safe_title(collection)
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return str(d)


def title_dir(title, kind="tv", collection=None, create=True):
    """<root>/<Collection>/Movies|TV Shows/<Title>/ — holds video, subs, nfo, artwork.

    A collection folder is always created; a standalone title gets one named after
    itself, so the depth is the same everywhere and scripts do not special-case.
    """
    d = hub_dirs(create=create)
    sub = d["movies_dirname"] if str(kind).lower().startswith("movie") else d["tv_dirname"]
    out = Path(collection_dir(collection or clean_title(title), create=create)) / sub / safe_title(title)
    if create:
        (out / ".work").mkdir(parents=True, exist_ok=True)   # drafts, never synced
    return str(out)


# Artwork and NFO go straight into the title folder, which is where Plex reads them.
# Never the current working directory — an agent's cwd is arbitrary.
workspace_for = title_dir
output_for = title_dir


# --- Plex/Jellyfin layout inside a title folder --------------------------------
# Kept here so every skill derives the same paths. Previously only cloud-librarian
# knew the convention, and each other skill invented its own destination — which is
# how the NAS and Drive copies ended up with different layouts.

JUNK = re.compile(
    r"\b(1080p|720p|480p|2160p|4k|bdrip|bluray|blu-ray|web-?dl|webrip|hdtv|dvdrip|"
    r"x264|x265|h\.?264|h\.?265|hevc|aac|ac3|flac|dual|remux|repack|proper)\b",
    re.IGNORECASE)


def clean_title(name):
    """Folder/display name with release tags and id markers stripped."""
    # Strip the year too: a collection spans years, so "Black Jack" must not become
    # "Black Jack (1993)". Must stay identical to core/settings.py:clean_title.
    out = re.sub(r"\{[^}]*\}|\[[^\]]*\]|\(\d{4}\)", " ", str(name or ""))
    out = JUNK.sub(" ", out)
    return re.sub(r"\s{2,}", " ", out).strip(" -_.") or "untitled"


def season_dir(title, season, kind="tv", collection=None, create=True):
    """<title>/Season NN — season 0 is Plex's folder for specials."""
    d = Path(title_dir(title, kind=kind, collection=collection, create=create)) / f"Season {int(season):02d}"
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return str(d)


def episode_filename(title, season, episode, ext="mkv", episode_title=None, quality=None):
    show = clean_title(title)
    name = f"{show} - S{int(season):02d}E{int(episode):02d}"
    if episode_title:
        name += f" - {clean_title(episode_title)}"
    if quality:
        name += f" [{quality}]"
    return f"{name}.{str(ext).lstrip('.')}"


def episode_path(title, season, episode, ext="mkv", episode_title=None, quality=None,
                 collection=None, create=True):
    return str(Path(season_dir(title, season, "tv", collection=collection, create=create))
               / episode_filename(title, season, episode, ext, episode_title, quality))


def movie_filename(title, year=None, ext="mkv", quality=None):
    name = clean_title(title)
    # The folder name usually already carries the year; appending it again gave
    # "Inception (2010) (2010).mkv".
    if year and f"({year})" not in name:
        name += f" ({year})"
    if quality:
        name += f" [{quality}]"
    return f"{name}.{str(ext).lstrip('.')}"


def movie_path(title, year=None, ext="mkv", quality=None, collection=None, create=True):
    return str(Path(title_dir(title, kind="movie", collection=collection, create=create))
               / movie_filename(title, year, ext, quality))


def subtitle_path(video_path, lang="vi", ext="srt", forced=False):
    """Plex sidecar rule: same stem as the video, plus a language code.

        Monster - S01E01 [1080p BluRay].mkv
        Monster - S01E01 [1080p BluRay].vi.srt

    The file must sit beside the video, which is why subtitles are the one thing that
    does not get redirected to a separate output directory.
    """
    v = Path(video_path)
    suffix = f".{lang}" + (".forced" if forced else "") + f".{str(ext).lstrip('.')}"
    return str(v.with_suffix("")) + suffix
