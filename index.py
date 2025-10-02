# Реализация Trie + autocomplete (min-heap / max-heap) + PriorityQueue менеджер запросов
# Выполняю демонстрацию на примере, включая тест скорости для 10_000 запросов.

import heapq
import random
import time
from collections import deque, defaultdict, Counter

# --- TrieNode и Trie ---
class TrieNode:
    __slots__ = ("children", "is_end", "frequency")
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.frequency = 0  # частота, если это конец слова

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, freq=1):
        """Добавить слово в Trie и установить/увеличить частоту.
        Если слово уже есть и передан freq, перезаписываем частоту (sum небезопасно для демонстрации).
        Здесь мы будем присваивать frequency = freq для явности — можно изменить на += для накопления.
        """
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.frequency = freq

    def search(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

    def _find_node(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

    def autocomplete(self, prefix, top_n=5, use_max_heap=False):
        """Возвращает top_n слов по частоте, начинающихся с prefix.
        use_max_heap=False -> поддерживаем min-heap размера top_n (чаще упоминается в задании).
        use_max_heap=True  -> используем 'макс-кучу' (через отрицательные частоты), что упрощает логику извлечения.
        """
        start = self._find_node(prefix)
        if not start:
            return []

        # DFS по поддереву, собираем (word, freq)
        results = []  # we won't store all results if we maintain heap on the fly
        # Use iterative stack to avoid recursion depth issues
        stack = [(start, prefix)]
        
        if use_max_heap:
            # We'll keep a normal list and use heapq.nsmallest on (-freq, word) or maintain max-heap
            heap = []  # will store (-freq, word)
            while stack:
                node, cur = stack.pop()
                if node.is_end:
                    heapq.heappush(heap, (-node.frequency, cur))
                for ch, child in node.children.items():
                    stack.append((child, cur + ch))
            # extract top_n from heap (largest freq -> smallest -freq)
            top = heapq.nsmallest(top_n, heap)
            return [word for _, word in top]
        else:
            # maintain min-heap of size at most top_n with (freq, word)
            heap = []
            while stack:
                node, cur = stack.pop()
                if node.is_end:
                    if len(heap) < top_n:
                        heapq.heappush(heap, (node.frequency, cur))
                    else:
                        # если оборот: если текущая частота > min в куче -> заменить
                        if node.frequency > heap[0][0]:
                            heapq.heapreplace(heap, (node.frequency, cur))
                for ch, child in node.children.items():
                    stack.append((child, cur + ch))
            # heap содержит top_n минимальной кучи => нужно вернуть отсортированно по убыванию частоты
            res = sorted(heap, key=lambda x: (-x[0], x[1]))
            return [word for _, word in res]

    def delete(self, word):
        """Удаление слова из Trie. Возвращает True если удалено, False если не найдено."""
        path = []  # (node, char)
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            path.append((node, ch))
            node = node.children[ch]
        if not node.is_end:
            return False
        # сбрасываем флаг конца слова и частоту
        node.is_end = False
        node.frequency = 0
        # удаляем ненужные узлы снизу вверх
        for parent, ch in reversed(path):
            child = parent.children[ch]
            if child.children or child.is_end:
                break
            del parent.children[ch]
        return True

# --- PriorityQueue менеджер ---
class PriorityQueue:
    def __init__(self):
        self._heap = []
        self._counter = 0  # чтобы сохранять FIFO порядок для одинаковых приоритетов

    def enqueue(self, request, priority=0):
        # higher numeric priority -> обслуживается раньше; используя min-heap, инвертируем приоритет
        heapq.heappush(self._heap, (-priority, self._counter, request))
        self._counter += 1

    def dequeue(self):
        if not self._heap:
            return None
        _, _, request = heapq.heappop(self._heap)
        return request

    def __len__(self):
        return len(self._heap)

# --- Демонстрация и тестирование ---

# Исходный словарь и частоты (пример из задания)
words_freq = {
    "apple": 10,
    "application": 5,
    "banana": 3,
    "book": 8,
    "binary": 1,
    "bee": 7,
    "bat": 4,
    "ball": 2
}

trie = Trie()
for w, f in words_freq.items():
    trie.insert(w, f)

# Создаём менеджер очереди и примеры запросов
pq = PriorityQueue()
pq.enqueue({"prefix": "app", "id": "req1"}, priority=1)   # VIP
pq.enqueue({"prefix": "b",   "id": "req2"}, priority=0)   # normal

# Обработка очереди и вывод результатов (используем min-heap вариант по умолчанию)
processed = []
while len(pq) > 0:
    req = pq.dequeue()
    prefix = req["prefix"]
    res = trie.autocomplete(prefix, top_n=5, use_max_heap=False)
    processed.append((req["id"], prefix, res))

print("Результаты обработки очереди (min-heap автодополнение):")
for pid, pref, out in processed:
    print(f"{pid} (prefix='{pref}') -> {out}")

# Тоже самое, но с использованием max-heap варианта (флаг use_max_heap=True)
pq2 = PriorityQueue()
pq2.enqueue({"prefix": "app", "id": "req1"}, priority=1)
pq2.enqueue({"prefix": "b",   "id": "req2"}, priority=0)

processed2 = []
while len(pq2) > 0:
    req = pq2.dequeue()
    pref = req["prefix"]
    res = trie.autocomplete(pref, top_n=5, use_max_heap=True)
    processed2.append((req["id"], pref, res))

print("\nРезультаты обработки очереди (max-heap автодополнение):")
for pid, pref, out in processed2:
    print(f"{pid} (prefix='{pref}') -> {out}")

# --- Дополнительное: удаление слова и повторный запрос ---
print("\nУдаляем слово 'application' и запрашиваем 'app' снова:")
deleted = trie.delete("application")
print("Удаление 'application':", deleted)
print("Autocomplete 'app' ->", trie.autocomplete("app", top_n=5))

# --- Тест скорости: 10_000 запросов ---
# Генерируем случайные префиксы на основе существующих слов (включая single-char prefixes)
all_prefixes = set()
for w in words_freq:
    for i in range(1, len(w)+1):
        all_prefixes.add(w[:i])
all_prefixes = list(all_prefixes)

# генерируем 10k запросов с приоритетами 0 или 1
N = 10_000
requests = []
for i in range(N):
    pref = random.choice(all_prefixes)
    pr = random.choices([0,1], weights=[0.8,0.2])[0]  # 20% VIP
    requests.append((pref, pr))

# помещаем в очередь
pq_perf = PriorityQueue()
for i, (pref, pr) in enumerate(requests):
    pq_perf.enqueue({"prefix": pref, "id": f"rq{i}"}, priority=pr)

# обработка и замер времени
start = time.perf_counter()
count = 0
while len(pq_perf) > 0:
    req = pq_perf.dequeue()
    _ = trie.autocomplete(req["prefix"], top_n=5)  # используем min-heap вариант
    count += 1
end = time.perf_counter()
duration = end - start

print(f"\nОбработано {count} запросов за {duration:.4f} сек (min-heap автодополнение).")
print(f"Среднее время на запрос: {duration / count * 1000:.4f} ms")
