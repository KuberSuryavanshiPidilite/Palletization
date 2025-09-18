
import streamlit as st
import matplotlib.pyplot as plt
from typing import List

class Rect:
    __slots__ = ("x", "y", "w", "h")
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = int(x); self.y = int(y); self.w = int(w); self.h = int(h)
    def fits(self, w: int, h: int) -> bool: return w <= self.w and h <= self.h

def overlap(a: Rect, b: Rect) -> bool:
    return not (a.x + a.w <= b.x or b.x + b.w <= a.x or a.y + a.h <= b.y or b.y + b.h <= a.y)

def subtract_rect(a: Rect, b: Rect) -> List[Rect]:
    inter_x1 = max(a.x, b.x); inter_y1 = max(a.y, b.y)
    inter_x2 = min(a.x + a.w, b.x + b.w); inter_y2 = min(a.y + a.h, b.y + b.h)
    if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
        return [a]
    res = []
    if a.x < inter_x1: res.append(Rect(a.x, a.y, inter_x1 - a.x, a.h))
    if inter_x2 < a.x + a.w: res.append(Rect(inter_x2, a.y, a.x + a.w - inter_x2, a.h))
    if a.y < inter_y1: res.append(Rect(inter_x1, a.y, inter_x2 - inter_x1, inter_y1 - a.y))
    if inter_y2 < a.y + a.h: res.append(Rect(inter_x1, inter_y2, inter_x2 - inter_x1, a.y + a.h - inter_y2))
    return [r for r in res if r.w > 0 and r.h > 0]

def score_bssf(free_rect: Rect, bw: int, bh: int):
    short_fit = min(free_rect.w - bw, free_rect.h - bh)
    long_fit = max(free_rect.w - bw, free_rect.h - bh)
    return (short_fit, long_fit, free_rect.w * free_rect.h)

def best_placement_maxrects(free_rects: List[Rect], orientations: List[tuple]):
    best = None; best_key = None
    for idx, fr in enumerate(free_rects):
        for (bw, bh) in orientations:
            if fr.fits(bw, bh):
                key = score_bssf(fr, bw, bh)
                if best is None or key < best_key:
                    best = (idx, (bw, bh)); best_key = key
    return best

def pack_layer(pallet_L, pallet_W, box_L, box_W, allow_rotation=True, spacing_mm=0):
    bw1, bh1 = box_L + spacing_mm, box_W + spacing_mm
    orientations = [(bw1, bh1)]
    if allow_rotation and box_L != box_W:
        orientations.append((bh1, bw1))
    free_rects = [Rect(0, 0, pallet_L, pallet_W)]
    placed_rects = []
    while True:
        cand = best_placement_maxrects(free_rects, orientations)
        if cand is None:
            break
        fr_idx, (bw, bh) = cand
        fr = free_rects[fr_idx]
        placed = Rect(fr.x, fr.y, bw, bh)
        placed_rects.append(placed)
        new_free = []
        for r in free_rects:
            if not overlap(r, placed):
                new_free.append(r)
            else:
                new_free.extend(subtract_rect(r, placed))
        free_rects = new_free
    return placed_rects

def draw_layer(rects, pallet_L, pallet_W):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, pallet_L)
    ax.set_ylim(0, pallet_W)
    for i, r in enumerate(rects):
        ax.add_patch(plt.Rectangle((r.x, r.y), r.w, r.h, fill=True, edgecolor='black', facecolor='skyblue'))
        ax.text(r.x + r.w/2, r.y + r.h/2, str(i+1), ha='center', va='center', fontsize=8)
    ax.set_title("Box Arrangement on First Layer")
    ax.set_aspect('equal')
    return fig

st.title("Palletization Planner")

pallet_L = st.number_input("Pallet Length (mm)", value=1200)
pallet_W = st.number_input("Pallet Width (mm)", value=1000)
max_height = st.number_input("Max Pallet Height (mm)", value=1600)
box_L = st.number_input("Box Length (mm)", value=300)
box_W = st.number_input("Box Width (mm)", value=200)
box_H = st.number_input("Box Height (mm)", value=250)
box_weight = st.number_input("Box Weight (kg)", value=10.0)
allow_rotation = st.checkbox("Allow Box Rotation", value=True)

if st.button("Calculate Palletization"):
    layer_boxes = pack_layer(pallet_L, pallet_W, box_L, box_W, allow_rotation)
    boxes_per_layer = len(layer_boxes)
    layers_by_height = max_height // box_H
    max_by_weight = int(1000 // box_weight)
    total_boxes = min(boxes_per_layer * layers_by_height, max_by_weight)
    pallet_weight = total_boxes * box_weight
    constraint = "Weight" if max_by_weight < boxes_per_layer * layers_by_height else "Height/Geometry"

    st.subheader("Results")
    st.write(f"Boxes per layer: {boxes_per_layer}")
    st.write(f"Max layers by height: {layers_by_height}")
    st.write(f"Max boxes by weight: {max_by_weight}")
    st.write(f"Total boxes on pallet: {total_boxes}")
    st.write(f"Pallet weight: {pallet_weight:.2f} kg")
    st.write(f"Constraint binding: {constraint}")

    st.subheader("First Layer Layout")
    fig = draw_layer(layer_boxes, pallet_L, pallet_W)
    st.pyplot(fig)
