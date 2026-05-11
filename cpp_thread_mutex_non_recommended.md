# C++ スレッド: メモリと並列処理（mutex まわり）

## 先に結論（やさしく）
- mutex は大事。でも、何でも mutex で囲む書き方はおすすめしない。
- `lock()` / `unlock()` を手で書くと、外し忘れで止まりやすい。
- まずは「データをなるべく共有しない設計」を目指す方が安全。

---

## 1. mutex って何をしてくれるの？
mutex には主に 2 つの役目があります。

- 同時に触らせない（順番待ちさせる）
- 最新の値を見えるようにする

イメージ:
- スレッドAが値を書いてから mutex を解放する
- そのあとスレッドBが同じ mutex を取る
- B からは A の書いた内容が見える

ポイント:
- 同じデータは、同じ mutex で守る

---

## 2. おすすめしない書き方

### 2-1. 手動で lock/unlock
```cpp
std::mutex m;
int counter = 0;

void bad() {
    m.lock();
    counter++;
    if (counter > 10) return; // unlock せず終わってしまう
    m.unlock();
}
```

なぜダメ？
- `return` や例外で `unlock()` を忘れやすい
- 1回忘れるだけで、他のスレッドが止まる

### 2-2. 読むだけだからロックしない
```cpp
std::mutex m;
int shared = 0;

int bad_read() {
    return shared; // 競合の可能性
}
```

なぜダメ？
- 他スレッドが同時に書くと、壊れた値や不安定な動作になる
- C++ ではこれは未定義動作

### 2-3. ロックの順番がバラバラ
```cpp
std::mutex a, b;

void t1() {
    std::lock_guard<std::mutex> lk1(a);
    std::lock_guard<std::mutex> lk2(b);
}

void t2() {
    std::lock_guard<std::mutex> lk1(b);
    std::lock_guard<std::mutex> lk2(a); // 互いに待って止まることがある
}
```

なぜダメ？
- ロック順が逆だと、デッドロックになりやすい

### 2-4. ロックしたまま重い処理
```cpp
std::mutex m;

void bad_io() {
    std::lock_guard<std::mutex> lk(m);
    // 重いI/Oや長い処理をここでやる
}
```

なぜダメ？
- 他スレッドの待ち時間が長くなる
- 並列にしている意味が薄れる

---

## 3. 最低限これを使う

### 3-1. lock_guard を使う
```cpp
std::mutex m;
int counter = 0;

void better() {
    std::lock_guard<std::mutex> lk(m);
    counter++;
}
```

よい点:
- 関数を抜けると自動で unlock される

### 3-2. 複数 mutex は scoped_lock
```cpp
std::mutex a, b;

void better_two() {
    std::scoped_lock lk(a, b);
}
```

よい点:
- 複数ロック時の事故を減らしやすい

### 3-3. ロック区間を短くする
- ロック中は共有データの読み書きだけ
- 重い計算や I/O はロックの外でやる

---

## 4. mutex だけに頼るのがしんどい理由
- ロックが大きいと遅くなる
- ロックが細かすぎると管理が難しい
- デッドロック調査が大変

現場でよく使う考え方:
- 共有データを減らす
- 単純な値は `std::atomic` を検討する
- キューやタスク実行に寄せる

---

## 5. まとめ
mutex は必要な道具です。  
でも「まず mutex」ではなく、**まず共有を減らす**が安全です。  
そのうえで必要な場所だけ mutex を使うのが、初心者にも失敗しにくい進め方です。
