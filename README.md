# 🎥 Nico-Style Comment Overlay 

# 🎥 ニコ生風コメント

---

## 📌 Overview

## 📌 概要

**English**
This project creates a *NicoNico-style floating comment overlay* that displays scrolling comments across the screen.

The overlay window is transparent, frameless, and designed to appear above games or applications.

**Japanese**
このプロジェクトは、画面上を流れる **ニコ生風コメントオーバーレイ** を実装したものです。

ウィンドウは透明・枠なしで、ゲームやアプリの上に重ねて表示できます。

---

## ✨ Features

## ✨ 特徴

### English

* Transparent Nico-style comment overlay
* Thousands of chaotic / meme / flaming comment variations
* Random font size for each comment
* Smooth animation using `QPropertyAnimation`

### Japanese

* 透明なニコ生風コメントオーバーレイ
* カオスで煽り気味なコメントを大量収録
* コメントごとにランダムなフォントサイズ
* `QPropertyAnimation` を使ったスムーズな横スクロール

---

## 🔧 How It Works

## 🔧 仕組み

### `CommentLabel`

**English:**
A QLabel subclass that creates a single floating comment with random font size and transparent background.

**Japanese:**
ランダムなフォントサイズと透明背景を持つ 1 個の流れるコメントを生成する QLabel の拡張。


### `NicoCommentOverlay`

**English:**
Main window that displays scrolling comments.
Comments move from right to left using animations.

**Japanese:**
コメントを右→左へ流すメインオーバーレイ。
アニメーションで滑らかにスクロールされる。

---
