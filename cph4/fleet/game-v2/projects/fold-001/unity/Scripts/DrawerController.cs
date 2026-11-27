using System;
using UnityEngine;

namespace FoldSpike
{
    // One drawer cell = 6 slots = 6 garments (EX-1: six tees standing up, zero headroom).
    // This spike map is 1 item per slot; the content spec's 1-4 slot widths are a later
    // change to OccupancyCost, not to the accept/reject contract.
    public sealed class DrawerController : MonoBehaviour
    {
        public const int SlotCount = 6;

        public Transform[] Slots = new Transform[SlotCount];

        // Fallback pitch so the prefab still lays out slots in a row when no anchors are wired.
        public float SlotPitch = 0.18f;

        public event Action<int, string> Placed;
        public event Action<int, string> PickedUp;

        // Fires when the cell is full. It is a hint, never a punishment: the caller shows
        // "这一格满了，先拿起一件" and nothing is lost, which is why the game has no loss screen.
        public event Action<string> ShelfFull;

        readonly string[] _items = new string[SlotCount];

        public int Capacity { get { return SlotCount; } }
        public int FreeSlots { get { return Capacity - Occupied; } }
        public bool IsFull { get { return Occupied >= Capacity; } }

        public int Occupied
        {
            get
            {
                int n = 0;
                for (int i = 0; i < SlotCount; i++) if (!string.IsNullOrEmpty(_items[i])) n++;
                return n;
            }
        }

        public string ItemAt(int slot)
        {
            if (slot < 0 || slot >= SlotCount) return null;
            return _items[slot];
        }

        public bool IsSlotOccupied(int slot)
        {
            return !string.IsNullOrEmpty(ItemAt(slot));
        }

        void Awake()
        {
            NormalizeSlots();
        }

        void NormalizeSlots()
        {
            if (Slots == null || Slots.Length != SlotCount)
            {
                Transform[] fixedSlots = new Transform[SlotCount];
                if (Slots != null)
                {
                    for (int i = 0; i < Slots.Length && i < SlotCount; i++) fixedSlots[i] = Slots[i];
                }
                Slots = fixedSlots;
                Debug.LogWarning("[FoldSpike] DrawerController expects exactly " + SlotCount + " slot anchors.");
            }
        }

        public bool TryPlace(string itemId)
        {
            if (string.IsNullOrEmpty(itemId)) return false;

            if (IsFull)
            {
                if (ShelfFull != null) ShelfFull(itemId);
                Debug.Log("[FoldSpike] drawer full, item kept in hand: " + itemId);
                return false;
            }

            int slot = FirstFreeSlot();
            if (slot < 0) return false;

            _items[slot] = itemId;
            if (Placed != null) Placed(slot, itemId);
            return true;
        }

        public bool TryPickUp(int slot, out string itemId)
        {
            itemId = null;
            if (slot < 0 || slot >= SlotCount) return false;
            if (string.IsNullOrEmpty(_items[slot])) return false;

            itemId = _items[slot];
            _items[slot] = null;
            if (PickedUp != null) PickedUp(slot, itemId);
            return true;
        }

        // Highest occupied slot first: the player naturally re-picks the thing that was just
        // slid in, and undo-by-hand should cost one tap.
        public bool TryPickUpLast(out int slot, out string itemId)
        {
            for (int i = SlotCount - 1; i >= 0; i--)
            {
                if (string.IsNullOrEmpty(_items[i])) continue;

                itemId = _items[i];
                slot = i;
                _items[i] = null;
                if (PickedUp != null) PickedUp(i, itemId);
                return true;
            }
            slot = -1;
            itemId = null;
            return false;
        }

        public Vector3 SlotWorldPosition(int slot)
        {
            if (Slots != null && slot >= 0 && slot < Slots.Length && Slots[slot] != null) return Slots[slot].position;
            float offset = (slot - (SlotCount - 1) * 0.5f) * SlotPitch;
            return transform.position + new Vector3(offset, 0f, 0f);
        }

        public int FirstFreeSlot()
        {
            for (int i = 0; i < SlotCount; i++) if (string.IsNullOrEmpty(_items[i])) return i;
            return -1;
        }

        public string[] Snapshot()
        {
            string[] copy = new string[SlotCount];
            Array.Copy(_items, copy, SlotCount);
            return copy;
        }

        public void ResetDrawer()
        {
            for (int i = 0; i < SlotCount; i++) _items[i] = null;
        }
    }
}
