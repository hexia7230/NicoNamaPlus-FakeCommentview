# -*- coding: utf-8 -*-
import sys
import random
import ctypes
import sounddevice as sd
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWinExtras import QtWin
from PyQt5.QtCore import QThread, pyqtSignal


class CommentLabel(QLabel):
    """ニコ生風コメントラベル"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: white; background: transparent;")
        
        # ランダムなフォントサイズ (12～32)
        font_size = random.randint(12, 32)
        font = QFont("MS Gothic", font_size, QFont.Bold)
        self.setFont(font)
        
        
        self.adjustSize()


class AudioWatcher(QThread):
    volumeSpike = pyqtSignal()  # 爆音時に発火

    def __init__(self, threshold=0.05, window=30, min_volume=0.01, cooldown=500, parent=None):
        super().__init__(parent)
        self.threshold = threshold
        self.window = window
        self.history = []
        self.min_volume = min_volume  # この値以下は無視
        self.cooldown = cooldown      # 発火間隔のクールダウン(ms)
        self.last_spike_time = 0
        self.running = True

    def run(self):
        import time

        def callback(indata, frames, time_info, status):
            if not self.running:
                return

            volume = np.sqrt(np.mean(indata**2))  # RMS音圧
            self.history.append(volume)
            if len(self.history) > self.window:
                self.history.pop(0)

            avg = np.mean(self.history)

            # 小さい音は無視
            if avg < self.min_volume:
                return

            # クールダウンチェック
            now = int(time.time() * 1000)  # 現在時刻(ms)
            if volume > self.threshold and (now - self.last_spike_time) > self.cooldown:
                self.volumeSpike.emit()
                self.last_spike_time = now

        with sd.InputStream(callback=callback):
            while self.running:
                sd.sleep(50)

    def stop(self):
        self.running = False


class NicoCommentOverlay(QWidget):
    """ニコ生風コメントオーバーレイウィンドウ"""
    
    # コメントリスト（拡張版）
    COMMENTS = [
        "やあ", "ひん", "は？", "おい", "いいね", "正解", "大卒", ";;", "きっしょ", "ねもうす",
        "4ね", "gm", "397", "ユダ", "チシア", "ｾｲｰ", "わろける", "実機", "沼", "素材", "あ", "夏野",
        "いいにほひ", "ﾓｴｰ", "わぁ！？", "よーーーし", "かっけぇ…",
        
        # ○○を具体的な言葉に置き換えたバリエーション
        "草サイコー", "配信サイコー", "主サイコー", "実況サイコー",
        "草最強！", "配信最強！", "主最強！", "ゲーム最強！",
        "草すべ", "配信すべ", "主すべ", "実況すべ",
        "草っ草", "主っ主", "配っ信", "実っ況",
        
        "いーや草だね", "いーや最高だね", "いーや神だね",
        "草だよなぁ！？", "最高だよなぁ！？", "神だよなぁ！？", "配信だよなぁ！？",
        "草！？", "主！？", "神！？", "配信！？",
        "草がいらぁ", "主がいらぁ", "神がいらぁ",
        "草もいるねぇ…", "主もいるねぇ…", "神もいるねぇ…",
        "草てらぁ", "主てらぁ", "配信てらぁ", "まずい",
        
        "なあ、配信しないか？", "なあ、ゲームしないか？", "なあ、休憩しないか？",
        "草は主のおかげ", "配信は主のおかげ", "神回は主のおかげ",
        
        "あ～ぐっちゃぐちゃだよ～^^", "やるおー^^", "やらないおー;;",
        "どりゃああああああ", "てめぇくぉのやろぉ〜〜〜〜！！",
        "てめぇぶっ５６す！！！ﾌﾌｯ",
        "よーーーーーーーーーーーーーーーーーーし！！！ﾌﾌｯ",
        "あ〜〜〜〜ぁ〜〜〜〜〜あぁぁ〜〜〜〜〜〜！！！（サイコパス）",
        "ずざああああああああああ",
        
        # さらに追加バリエーション
        "888888", "wwwwww", "うぽつ", "乙", "おつかれ", "初見です",
        "最高かよ", "神回", "草生える", "やばい", "えぐい", "つよい",
        "ヤバすぎて草", "これは草", "わかる", "それな", "まじか", "うそやん",
        "ｷﾀ━━━━(ﾟ∀ﾟ)━━━━!!", "ﾜﾛﾀ", "ｸｿﾜﾛ", "腹筋崩壊", "センスの塊",
        "プロかよ", "才能の無駄遣い", "これすき", "好き", "すこ", "尊い",
        "泣いた", "感動した", "鳥肌", "震えた", "涙が止まらない",
        "ありがとう", "最高です", "面白すぎる", "笑った", "爆笑",

            "おまえ誰？ｗ", "だれだよｗ", "なにいってんのｗ", "IQ2", "脳溶けてて草",
    "しょーもなｗ", "秒で草", "小学生以下ｗ", "バカ発見ｗ", "終わってて草",
    "違うそうじゃないｗ", "もうやめろｗ", "地獄ｗ", "地獄配信で草",
    "限界集落みたいなコメ欄", "治安終わってる", "民度ゼロすぎｗ",

    "はいバカｗ", "脳みそ蒸発してて草", "IQマイナス", "脳死プレイｗ",
    "話通じないレベルｗ", "こわｗ", "逆に好きｗ", "おまえ向いてないｗ",

    "末期ニコ動みたいなノリ好き", "ここ末期すぎるｗ", "コメントの治安大崩壊",
    "コメント欄が魔境すぎる", "汚物祭りｗ", "語彙力崩壊選手権",
    "何言ってんだこいつ選手権", "バカしかいねぇｗ", "IQ溶かされる配信",

    "うるせぇｗ", "だまれｗ", "また草", "草しか言えん病気ｗ",
    "脳死ｗ", "気合で読めｗ", "意味不明で草", "語彙力0", "語彙力きえた",

    "もう終わりだよこの配信", "完全崩壊ｗ", "限界ｗ", "逆に天才",
    "草ァ！", "頭悪すぎて好き", "理解不能ｗ", "なんでそうなるｗ",

    "あーIQ下がる音した", "脳がとろける", "これが限界視聴者", "魔境コメ欄へようこそ",
    "馬鹿の集会", "IQ偏差値3", "脳みそ捨ててきた？", "無法地帯ｗ",

      "脳みそ溶けたｗ", "頭おかしいｗ", "終わってるｗ", "バカしかいねぇｗ", "IQ1",
    "理解不能ｗ", "意味不明で草", "語彙力0", "語彙力きえた", "狂気ｗ",
    "完全に崩壊ｗ", "魔境コメ欄", "無法地帯ｗ", "逆に天才ｗ", "脳死プレイｗ",
    "頭悪すぎて草", "なんでそうなるｗ", "馬鹿の集会ｗ", "限界ｗ", "もう終わりｗ",
    "コメント欄カオスｗ", "地獄ｗ", "治安ゼロｗ", "バカ確定ｗ", "秒で草",
    "小学生かな？ｗ", "意味不明すぎｗ", "脳みそ足りてないｗ", "IQマイナスｗ",
    "やべぇｗ", "狂気の沙汰ｗ", "脳溶かし実況ｗ", "理解不能レベルｗ",
    "末期ニコ動再現ｗ", "草ァ！", "脳死ｗ", "おまえ誰ｗ", "何言ってんだこいつｗ",
    "バカしかいないｗ", "限界集落コメ欄ｗ", "頭大丈夫かｗ", "脳みそ破壊ｗ",
    "コメントが地獄ｗ", "逆に好きｗ", "脳死で草ｗ", "IQ下がる音ｗ",
    "理解力皆無ｗ", "終末感ｗ", "配信者の脳みそ心配ｗ", "狂気のコメントｗ",
    "やばすぎて草ｗ", "限界視聴者ｗ", "頭溶けたｗ", "魔境ｗ", "地獄絵図ｗ",
    "脳がとろけるｗ", "もうやめろｗ", "意味不明すぎて草ｗ", "馬鹿すぎるｗ",
    "コメント欄の終焉ｗ", "IQ溶かす実況ｗ", "狂気しかないｗ", "脳みそ死んでるｗ",
    "カオスｗ", "バカ祭りｗ", "治安崩壊ｗ", "脳みそ消失ｗ", "理解不能コメントｗ",

     ";;", "まずい;;", "ひん;;", "ｗｗｗｗｗ", "ｗｗ", "ｗｗｗｗｗｗｗｗｗｗｗｗｗ",
    "ひんひんｗｗ", ";;ｗ", "ｗｗｗｗ", "ｗｗｗｗｗｗｗ", "やめべ",
    "ｗｗｗｗｗｗ", ";;ｗｗ", "あ、", "ｗｗｗｗｗｗｗｗ", "ｗｗｗｗｗｗｗｗｗ",
    "ひんｗｗｗ", ";;;;", "ｗｗｗｗｗｗｗｗｗｗ", "ｗｗｗｗｗｗｗｗｗｗｗ", "ｗｗｗｗ",
    "ｗｗｗｗｗｗｗ", "やめべ；；", "あ、まずい", "ｗｗｗｗｗｗｗｗｗｗ", "ｗｗｗｗｗｗｗｗ",
    "ひんｗｗｗｗｗ", "；；；；", "ｗｗｗｗｗｗｗｗｗｗｗｗｗｗｗ", "ｗｗｗｗｗｗｗｗｗｗｗ",
    "ひん；；", "ｗｗｗｗｗｗｗｗｗｗｗｗ", ";;ｗｗｗ", "あ、", "ｗｗｗｗｗｗｗｗｗ",
    "まずいｗｗｗ", "ｗｗｗｗｗｗｗｗｗｗｗｗ", "ｗｗｗｗｗｗｗｗ", "あ、；；", ";;ｗｗｗｗ",

     "みんな、見てるか！？", "この展開、信じられるか？", "どう思う、これ！？", "誰か助けて状況説明して！", 
    "ここからどうなると思う？", "やばい、これ止められる奴いる？", "心の準備はできてるか！？", "これ、理解できる奴いる？", 
    "みんな、息してる！？", "もう戻れないぞ…",

    "演出ヤバすぎｗｗ", "ここ天才か？", "想像の上をいくｗ", "この瞬間心震えた", 
    "発想力が破壊的すぎる", "ここでこう来るの天才ｗ", "見てるだけで脳汁出るｗ", "感情が爆発した", 
    "才能の塊ｗｗｗ", "ここまで作り込むとかやばい", "完全に心掴まれた", "震える…",
    "赤西仁",
"悪よ去れ",
"当たり枠",
"あったけえなあ…",
"アデノイダー",
"アパチャイ",
"アブ4ね",
"甘いパン",
"抗うな",
"歩くクレヨン",
"いいにほい",
"いいね正解大卒",
"いいんじゃないかぁ！？",
"イキイキ働く障がい者！",
"いけるっしょ",
"一応大卒",
"いっちゃう",
"一発でいいわけ。俺達は。",
"井出貴之!?",
"祈らなきゃ…",
"インターネットヒーロー",
"ヴィレヴァン?",
"うーちゃん!?",
"兎田ぺこ、ら",
"おならぷーしちゃった",
"おはスタ?",
"お前がやれよぉ！",
"お前を逮捕しに行く",
"キーファアアアアアおいしいよおおおおお?",
"効いてる効いてる",
"絆?",
"キヨの方がうまい",
"コカトリス",
"ここがいいんでしょぉぉおおお！？",
"ここで大きい声出すよなぁ！？",
"ここで暮らそう",
"ここにいたのか…?",
"ここを俺の縄張りとす！?",
"孤独ちゃん",
"コンテンツ-女=繁栄",
"コントローラー逆",
"こんな暮らしも悪くないね",
"さ",
"最後のピース",
"最後の一撃は、切ない。?",
"サワムラー",
"さわらあああああ生きてるかあああああ！？?",
"サンキュな",
"ジーパーアンモ",
"塩の許可とったの？?",
"ジェクト",
"手動館山",
"実機止め",
"シャーク",
"じゃがいも",
"写真枠",
"ジャッキーカルパス",
"喋りの暴走機関車",
"ジャンヌ",
"ジャンボ",
"ジュエル?",
"手動館山",
"障害者合コン",
"じょうよわﾊｹｰﾝしますた",
"ショーーーーーーン！?",
"死んどるやんけぇ！？",
"シンはジェクトだ",
"スイカゲーム",
"スーツマン?",
"スーパーポテト",
"ｽﾁ",
"すべ?",
"すべて無に帰す?",
"すべるんやー",
"スメアゴル",
"ｾｲｰ",
"正解",
"声優?",
"セピア",
"セピアウイルス?",
"攻めのルンバ",
"セルビア?",
"戦士が…戦ってる…？",
"先生",
"仙田?",
"相馬亘",
"速読英単語",
"【速報】伊良部自殺",
"ｿﾅｺﾄﾅｲ",
"その角度はフェアじゃないねぇ…?",
"尊師",
"た",
"だいじょーぶ！330分延長してあっから?",
"大卒",
"大地讃頌",
"第7サティアン",
"チーツ",
"違う！デコイよ！?",
"梨スレ",
"梨民",
"なっさん",
"夏野バカすぎワロタ",
"ﾅﾐﾀﾞﾎﾟﾛﾘﾁｬﾈﾗ?",
"ねもうすちゃんねる",
"脳?",
"ノンデリ",
"は",
"ぱぁ！？?",
"ばーーーーーーーか?",
"はーい論破しまーす",
"婆さん、外すぜ！?",
"はいっ！?",
"はいかいいえで答えて",
"はい、ワキガの匂いがします。?",
"パイクマン",
"ハイパー面白い君",
"場数理論?",
"バカでもユニでもできる?",
"爆破",
"バターな",
"発展途上国",
"鼻くそ氷山?",
"ハナチャン",
"パニックになってしもてん！",
"ハネウマライダー選手権?",
"馬場豊",
"浜田?",
"ハラマキ",
"バルナバ",
"晴れたああああ?",
"半島の血が騒ぐ",
"ひいいいいごめんなさいいいいい",
"ひかりいいいいいいいい?",
"ヒゲガマガエルかなぁ！？?",
"糞づまりでも～俺は気にしないぜよ～♪",
"ペースメーカー?",
"ぺこ純",
"ペス",
"ベリアル",
"ホーキンス?",
"防空壕",
"頬骨",
"募金詐欺?",
"ポケモンで言ったら5分の1",
"ぽこた",
"ホモ",
"ま",
"まいしゃん?",
"マーリン?",
"魔作",
"まずい要素なし?",
"もう俺たちを解放してくれ",
"もうブックマーク消しませんか？?",
"靖国で会おう?",
"やってるー？^^",
"山田和樹",
"やまだひさし?",
"やめべ",
"やらないおー;;?",
"やるお！?",
"ヤングタウンNEXT",
"やんよ",
"ユイガイガイ",
"遊戯王の民?",
"ユウナちゃん！時間がねぇ！?",
"夕飯にするか？",
"ユダ",
"ﾕ､ﾙｽ?",
"ユンボ",
"よく寝たぜ",
"よっちゃん",
"よっちゃんだよー＾＾",
"ら・わ",
"リモートコントロールダンディ?",
"ルナ",
"レイモンド",
"レジディア",
"録画班?",
"ロレックス?",
"ロマンチック選手権",
"わぁ！？",
"ワキガキ",
"ワシボン",
"ワッカは降りろよ、機械だぞ",
"わっちゃん",
"わらぁ鬼の子だぁ…?",
"わり、俺死んだ?",
"ワロケル?",
"ﾜﾛﾛﾛﾛｰ?",
"ワンダーボーイ",
"ﾝｼﾞｮﾜﾘｨ",
"んだよ！！?",
"英数",
"2.17事件",
"2時から?",
"gm?",
"gmのテーマ",
"わらぁ鬼の子だぁ…?",
"わり、俺死んだ?",
"キヨのほうが上手い",
"わ、ざと へった",
"あー、もう許せない",
"それ違うよね？",
"え、これマジでやるの？",
"やっぱり来たか",
"うそだろ…",
"ここからが本番",
"まさかの展開",
"キヨのほうが上手い",
"わ、ざと へった",
"それマジで下手すぎ",
"いや、それセンス無さすぎだろ",
"え、何その雑プレイ",
"は？なにしてんの？",
"ほんとにそれで満足してんの？",
"いや、俺でももうちょいマシだわ",
"ふざけんなよ",
"それ逆に恥ずかしくない？",
"おい、やめろよそれ",
"下手すぎて草",
"マジで頭使えよ",
"えー、それ意味あるの？",
"ちょっと、死ぬ気でやれや",
"雑魚すぎんだろ",
"それじゃ勝てるわけねぇ",
"何やってんだお前",
"舐めてんのか？",
"ふざけてる場合か",
"それ全然ダメじゃん",
"いや、笑えないレベルで下手",
"まじでやばすぎ",
"は？何の考えもないのか",
"ちょっと黙れ、邪魔だ",
"え、頭大丈夫？",
"何その中途半端プレイ",
"うわ、やばすぎ笑えねぇ",
"全力出せや",
"それ、失敗すぎるだろ",
"下手すぎて笑うしかねぇ",
"マジでセンスなさすぎ",
"いや、さすがに酷いわ",
"えー、それ正気？",
"お前それで勝てると思ってんの？",
"やる気あるのか？",
"雑すぎて見てられん",
"ふざけんなよおい",
"下手すぎて草も生えん",
"その動き、マジで意味不明",
"ちょっと黙ってろ邪魔",
"何してんのか全然わからん",
"それ、センスゼロじゃん",
"マジで頭沸いてんの？",
"お前、ゲーム舐めてるだろ",
"いや、ありえんだろその動き",
"全然ダメだな",
"え？それ本気でやってんの？",
"頭使えや",
"ふざけた動きすぎ",
"雑すぎて心折れる",
"いや、ほんとに酷い",
"それ、見る価値ないぞ",
"マジで下手すぎ",
"お前何も考えてないだろ",
"は？雑すぎんだろ",
"いや、これ完全に負け確定",
"ふざけんなって",
"それ、何の意味もないだろ",
"ちょっとは考えろや",
"えー、何やってんの",
"下手すぎてイライラする",
"おい、ちゃんとやれ",
"いや、雑すぎて萎える",
"それマジで笑えねぇ",
"何やってんだお前マジで",
"ちょっと黙れ邪魔",
"頭おかしいだろそれ",
"雑すぎてゲーム崩壊",
"は？意味わからん",
"いや、それマジで酷い",
"お前さ、舐めすぎだろ",
"マジで下手すぎて泣ける",
"え、マジでそれやるの？",
"いや、全然ダメだろ",
"ふざけんなよマジで",
"おい、ちょっと考えろ",
"雑すぎて笑えねぇ",
"何それ、センス皆無",
"全然ダメすぎる",
"お前、頭回ってないだろ",
"いや、ふざけすぎだろ",
"マジで雑魚すぎ",
"は？それやる意味あるの？",
"ちょっと黙ってろ邪魔すぎ",
"いや、見てて辛いわ",
"雑すぎて草も生えん",
"お前、ほんとゲーム舐めすぎ",
"マジで頭悪すぎ",
"え、何考えてんの",
"ふざけんなやマジで",
"雑すぎて吐きそう",
"おい、もうちょいマシにしろ",
"いや、酷すぎて見れん",
"全然成長してねぇじゃん",
"それ、逆に恥ずかしいぞ",
"ふざけんなよお前マジで",
"雑すぎて萎える",
"ちょっと考えろやクソ",
"お前の動き、意味わからん"
    ]
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.comments = []  # アクティブなコメントのリスト

        self.audio_watcher = AudioWatcher()
        self.audio_watcher.volumeSpike.connect(self.spawn_burst_comment)
        self.audio_watcher.start()


        
        # コメント生成タイマー（500ms～1500msの間隔でランダム生成）
        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self.spawn_comment)
        self.spawn_timer.start(random.randint(500, 1500))
        
        # 定期的にタイマー間隔を変更
        self.interval_timer = QTimer(self)
        self.interval_timer.timeout.connect(self.randomize_spawn_interval)
        self.interval_timer.start(5000)

    BURST_COMMENTS = [
        "どりゃああああああああ", "うおおおおおおおお", "すげええええええええ",
        "あああああああああああああああああああああああああ", "ｗｗｗｗｗｗｗｗｗｗｗｗｗｗｗｗｗｗ",
        "！？？！？！？", "は？？？？", "きたああああああああ",
    ]

        
    def init_ui(self):
        hwnd = self.winId().__int__()



        """UIの初期化"""
        # フルスクリーンで表示
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # ウィンドウフラグの設定
        self.setWindowFlags(
            Qt.FramelessWindowHint |          # フレームレス
            Qt.WindowStaysOnTopHint |         # 常に最前面
            Qt.Tool |                         # タスクバーに表示しない
            Qt.WindowTransparentForInput      # マウス透過
        )
        
        # 背景を完全透明に
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.setStyleSheet("background: transparent;")

        #Win32で最前面化
        hwnd = self.winId().__int__()
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOACTIVATE = 0x0010
        HWND_TOPMOST = -1
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        )

        
    def spawn_comment(self):
        """コメントを生成"""
        # 同時表示数を10～20に制限
        if len(self.comments) >= 20:
            return
        
        # ランダムなコメントテキストを選択
        text = random.choice(self.COMMENTS)
        
        # コメントラベルを作成
        comment = CommentLabel(text, self)
        
        # ランダムなY座標（上から10%～90%の範囲）
        screen_height = self.height()
        y_pos = random.randint(int(screen_height * 0.1), int(screen_height * 0.9))
        
        # 画面右端の外側から開始
        start_x = self.width()
        comment.move(start_x, y_pos)
        comment.show()
        
        # アニメーション設定（右→左へ移動）
        animation = QPropertyAnimation(comment, b"pos")
        animation.setDuration(random.randint(8000, 12000))  # 8～12秒で横断
        animation.setStartValue(QPoint(start_x, y_pos))
        animation.setEndValue(QPoint(-comment.width(), y_pos))  # 左端の外まで
        animation.setEasingCurve(QEasingCurve.Linear)
        
        # アニメーション終了時にコメントを削除
        animation.finished.connect(lambda: self.remove_comment(comment, animation))
        
        animation.start()
        
        # リストに追加
        self.comments.append((comment, animation))

    def spawn_burst_comment(self):
        """音量スパイクで複数コメントを生成"""
        for _ in range(random.randint(3, 7)):
          text = random.choice(self.BURST_COMMENTS)
          comment = CommentLabel(text, self)
        
        # Y座標ランダム
          y_pos = random.randint(int(self.height() * 0.1), int(self.height() * 0.9))
          start_x = self.width()
          comment.move(start_x, y_pos)
          comment.show()

        # アニメーション設定
          animation = QPropertyAnimation(comment, b"pos")
          animation.setDuration(random.randint(4000, 8000))  # 4～8秒で横断
          animation.setStartValue(QPoint(start_x, y_pos))
          animation.setEndValue(QPoint(-comment.width(), y_pos))
          animation.setEasingCurve(QEasingCurve.Linear)
          animation.finished.connect(lambda: self.remove_comment(comment, animation))
          animation.start()
        
          self.comments.append((comment, animation))



        
    def remove_comment(self, comment, animation):
        """コメントを削除"""
        try:
            self.comments.remove((comment, animation))
            comment.deleteLater()
        except (ValueError, RuntimeError):
            pass
    
    def randomize_spawn_interval(self):
        """コメント生成間隔をランダムに変更"""
        self.spawn_timer.setInterval(random.randint(500, 1500))







def main():
    app = QApplication(sys.argv)
    
    # オーバーレイウィンドウを作成・表示
    overlay = NicoCommentOverlay()
    overlay.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()