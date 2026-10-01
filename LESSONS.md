# Lessons for KOML

Workflow state is a reduction over ordered events; replay requires storing the exact inputs and the ordering contract. Exact duplicate delivery differs from a conflicting duplicate and deserves separate treatment.

The synthetic experiment validated the assumption that deterministic event reduction can match independent status and allocation ground truth exactly. Changing a completion event to a failure changed the measured totals, showing that reports compute results rather than reading expectations. Real operational usefulness remains unvalidated.

Operating rule for future builds: define ordering, duplicate policy, transition rules, and an independent oracle before adding persistence or external workers. Keep real-use verdicts pending until the evidence window is actually observed.
