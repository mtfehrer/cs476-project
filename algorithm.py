import heapq

warehouse = [[[], 0, [], 0, []],
             [0,  0, 0,  0, 0],
             [[], 0, [], 0, []],
             [0,  0, 0,  0, 0],
             [[], 0, [], 0, []]]

def is_valid(pos, visited):
    if (pos[0] >= 0 and pos[0] < len(warehouse) and
        pos[1] >= 0 and pos[1] < len(warehouse[0]) and 
        pos not in visited and
        warehouse[pos[0]][pos[1]] == 0):
        return True
    return False

def manhattan_distance(x, y):
    return abs(x[0] - y[0]) + abs(x[1] - y[1])

def a_star(src, dest):
    heap = []
    heap.append((0, src))
    visited = set()
    path = []

    while heap:
        _cost, pos = heapq.heappop(heap)
        visited.add(pos)
        path.append(pos)

        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            next_pos = (pos[0] + dx, pos[1] + dy)
            if is_valid(next_pos, visited):
                heapq.heappush(heap, (manhattan_distance(src, pos) + manhattan_distance(next_pos, dest), next_pos))
    
    return path

print(a_star((1, 0), (3, 4)))