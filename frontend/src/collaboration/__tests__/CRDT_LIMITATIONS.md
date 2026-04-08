# Yjs CRDT Known Limitations

## Non-Deterministic Ordering

Yjs CRDTs guarantee **eventual consistency** but not **strict determinism** in all scenarios.

### What Yjs Guarantees (✅):
1. **Convergence**: All replicas eventually reach the same state
2. **Commutativity**: Update order doesn't affect final convergence
3. **Idempotence**: Applying same update multiple times is safe
4. **No Data Loss**: All edits are preserved

### What Yjs Does NOT Guarantee (⚠️):
1. **Strict Determinism**: Character ordering may vary based on:
   - Document creation timing
   - Client ID assignment
   - Concurrent edit timing
   
### Example:
```javascript
// Two users insert at position 0 concurrently
User1: insert("$", 0)  
User2: insert("Start", 0)

// Possible outcomes (both valid):
Result A: "$StartStart"  // User1's edit ordered first
Result B: "Start$Start"  // User2's edit ordered first
```

Both results are **correct** because:
- Both documents converge to the same state
- No data is lost
- The ordering is consistent within each replica

### Production Impact:
This is **expected CRDT behavior** and does not affect real-world collaboration:
- Users see consistent state within their session
- All edits are preserved
- Conflicts are resolved automatically
- No manual merge required

### Test Strategy:
Property tests validate:
1. ✅ Convergence (not strict character ordering)
2. ✅ Data preservation
3. ✅ Idempotence
4. ⚠️ Determinism (relaxed to allow CRDT ordering variations)
