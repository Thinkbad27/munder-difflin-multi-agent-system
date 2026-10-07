# Reflection Report: Munder Difflin Multi-Agent Ordering System

## 1. System Overview

The system is built with `smolagents` (`ToolCallingAgent` + `managed_agents`) and consists of four agents:

- **Orchestrator** — receives each customer request and delegates to the three specialist agents below, then synthesizes a single customer-facing response.
- **Inventory Agent** — checks current stock (`check_stock`, `check_full_inventory`), estimates supplier delivery timelines (`estimate_restock_arrival`), and places restock orders (`place_restock_order`).
- **Quoting Agent** — maps free-text item descriptions to exact catalog names, checks quote history for pricing precedent (`find_similar_past_quotes`), and checks current availability (`check_available_items`).
- **Sales Agent** — confirms delivery windows and cash health (`confirm_delivery_window`, `check_cash_health`, `get_financial_report`), and finalizes or rejects the order (`finalize_sale`).

All seven required helper functions (`create_transaction`, `get_all_inventory`, `get_stock_level`, `get_supplier_delivery_date`, `get_cash_balance`, `generate_financial_report`, `search_quote_history`) are used by at least one tool across the four agents, and the total agent count (4) stays within the 5-agent limit.

## 2. Testing Summary

The system was run against all 20 sample requests in `quote_requests_sample.csv` (dated 2025-04-01 through 2025-04-17). The run produced a mix of outcomes:

- **Finalized orders**: several requests (e.g. requests 4, 11, 14, 18) were reported as finalized, each with a transaction ID. Section 3 explains why those reports have to be checked against the database rather than taken at face value.
- **Rejected orders**: the majority of requests were rejected, for a mix of legitimate reasons — insufficient stock that could not be restocked in time, delivery dates that fell after the customer's deadline, and (for large orders) insufficient cash balance to proceed.

This satisfies the project's requirement of producing both successful and rejected outcomes in `test_results.csv`, and demonstrates that the orchestration logic correctly threads inventory, pricing, and financial constraints into the final decision rather than approving every request.

## 3. Limitations Discovered During Testing

Several rounds of testing surfaced a specific, recurring failure pattern that is worth documenting honestly:

**a) Cross-agent narrative drift.** Information between the orchestrator and its managed agents is passed as natural-language text, not structured data. Early test runs showed the final response occasionally restating a price or delivery date that did not match what the underlying tool had actually returned (e.g. a delivery date reported as a plausible-but-wrong year, or a total price that did not equal unit price × quantity).

**b) Prompt constraints reduce but do not eliminate fabrication.** Adding explicit instructions requiring agents to quote tool outputs verbatim, and to include the transaction ID and price returned by `finalize_sale` in any "success" claim, measurably improved output quality — but did not fully solve the problem. In a later test run, some "successfully finalized" responses included transaction IDs and totals that did not show a matching change in the cash balance snapshot taken on the request date, which suggests (but does not prove, because agents choose the transaction date themselves and a sale can appear in a later day's balance) that the model produced a response in the *correct format* the instructions asked for, without it being grounded in an actual tool call result. This is a useful, concrete illustration of a general limit of prompt engineering: instructions can shape the *shape* of an output, but cannot by themselves guarantee that every stated fact is backed by a real function call.

**c) Occasional date hallucination persisted at low frequency.** Even after adding rules forbidding dates not sourced from a tool's return value, one isolated case still surfaced an out-of-range year. This is consistent with `gpt-4o-mini` not following instructions with 100% reliability, rather than an error in the prompt design itself.

## 4. Suggested Improvements

1. **Replace natural-language hand-offs with structured data.** Instead of agents returning free-text summaries to the orchestrator, each specialist agent should return a small structured object (e.g. a JSON payload with explicit `item`, `quantity`, `unit_price`, `total_price`, `delivery_date`, `transaction_id` fields). The orchestrator would then assemble the customer-facing message by inserting these values directly, rather than asking the LLM to "remember and restate" them — removing the main channel through which numbers currently drift or get fabricated.

2. **Add an automated post-run reconciliation step.** After `run_test_scenarios()` completes, a separate script (or an `EvaluationAgent`, following the same pattern used in the Agentic Workflow project) should query the `transactions` table directly and cross-check every response claiming a "finalized" sale against an actual matching row in the database. Any response whose claimed transaction ID, item, or price cannot be found in the ledger should be flagged for review rather than accepted at face value. This closes the gap that prompt-level instructions alone could not close.

3. **Tighten structured output validation for critical fields.** Using a Pydantic model (as in the earlier itinerary-planning project) to constrain the agent's final response — particularly for dates and prices — would allow invalid values (e.g. a date outside the expected 2025 range, or a price that doesn't reconcile with unit price × quantity) to be caught and automatically retried before being written to `test_results.csv`, rather than relying solely on instruction-following.

## 5. Conclusion

The multi-agent system successfully orchestrates inventory, pricing, and sales decisions across three specialist agents and produces a realistic mix of finalized and rejected orders. The main lesson from this project is that reliable multi-agent systems need more than well-crafted prompts: as agents hand information to one another in natural language, small inaccuracies can compound, and only a combination of clear instructions *and* independent, code-level verification against ground-truth state (the database) can catch what prompting alone misses.
