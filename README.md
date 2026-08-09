# 🏥 Hospital Patient Billing System

**Assignment 05 — MIJ Technologies Python Programming Series**
*From Complete Beginner to Software Engineer Foundations — Functions, Loops & Conditionals*

A command-line program that simulates a hospital receptionist's billing desk: it records patient visits, calculates service charges using multi-tier pricing rules that differ per service type, applies insurance coverage with provider-specific rates and caps, prints an itemized patient bill, and produces a daily hospital revenue report.

---

## 🎯 Overview

This project is **Assignment 5**, the most involved assignment in the series so far. Unlike earlier assignments where pricing was a single flat lookup, this one requires **branching, tiered pricing logic per service type** — each of the four service types (Consultation, Emergency, Surgery, Admission) has its own multi-step charge structure, several of which are themselves tiered by duration. On top of that, insurance coverage introduces percentage-based deductions with per-provider maximum caps that must be enforced with `min()`.

| | |
|---|---|
| **Topics Covered** | Functions, Loops & Conditionals |
| **Difficulty** | Very Hard |
| **Total Marks** | 30 |
| **Estimated Time** | 6–8 hours |

---

## ✨ Features

- **Repeated patient entry** — the receptionist can log as many patients as needed in a single session before stopping.
- **Service-type-aware input** — asks for **hours** for Consultation/Emergency/Surgery, or **days** for Admission, based on the selected service type.
- **Insurance-aware provider logic** — if insurance status is "No", the provider is automatically set to `None` without prompting; otherwise the provider is validated against the accepted list (case-insensitive, normalized to a consistent display form).
- **Per-service tiered pricing**, each with its own step-by-step calculation trace:
  - **Consultation** — flat first-hour rate, then a lower rate per additional hour.
  - **Emergency** — a higher rate for the first two hours, then a reduced rate per additional hour.
  - **Surgery** — a flat rate determined by whether duration crosses a 3-hour threshold (Minor vs Major).
  - **Admission** — a three-tier daily rate that decreases as length of stay increases (days 1–3, days 4–7, day 8+).
- **Insurance coverage engine** — looks up each provider's coverage percentage and maximum cap from a single table, applies `coverage = min(total × rate, cap)`, and computes the patient's remaining balance.
- **Itemized bill display** — separate, boxed sections for the service charge breakdown, insurance coverage, and final patient bill, with Surgery bills additionally labeled Minor/Major.
- **Daily hospital report** — total patients, total revenue, average bill, a full per-service-type breakdown, insurance status counts (with/without insurance), and the most common insurance provider (with tie handling).
- **Defensive input validation** — empty fields, non-integer durations, invalid service types, and invalid providers are all caught and re-prompted rather than crashing the program.
- **Graceful exit handling** — `Ctrl+C` / `Ctrl+D` are caught so the program never crashes on interrupt.

---

## 🧮 Business Rules

**Service Pricing**

| Service Type | Pricing Structure |
|---|---|
| Consultation (per hour) | First hour: 50,000 UGX. Each additional hour: 30,000 UGX |
| Emergency (per hour) | First 2 hours: 100,000 UGX/hr. Additional hours: 80,000 UGX/hr |
| Surgery (flat rate) | Minor (< 3 hrs): 500,000 UGX. Major (≥ 3 hrs): 1,200,000 UGX |
| Admission (per day) | Days 1–3: 150,000/day. Days 4–7: 120,000/day. Beyond day 7: 100,000/day |

**Insurance Coverage**

| Provider | Coverage | Maximum Cap |
|---|---|---|
| NHIF | 60% of total bill | 300,000 UGX |
| AAR | 80% of total bill | No limit |
| Jubilee | 70% of total bill | 500,000 UGX |
| None | 0% (patient pays 100%) | N/A |

```
Insurance Coverage = min(Total Bill × Coverage %, Maximum Cap)
Patient Pays        = Total Bill - Insurance Coverage
```

**Worked Example — Admission, 10 days, NHIF**
```
Days 1-3:  3 x 150,000 = 450,000
Days 4-7:  4 x 120,000 = 480,000
Days 8-10: 3 x 100,000 = 300,000
TOTAL BILL = 1,230,000 UGX

NHIF (60%): 1,230,000 x 0.60 = 738,000 -> CAPPED at 300,000
Patient Pays: 1,230,000 - 300,000 = 930,000 UGX
```

**Worked Example — Surgery, 4 hours, AAR**
```
Duration >= 3 hrs -> Major Surgery = 1,200,000 UGX
AAR (80%): 1,200,000 x 0.80 = 960,000 UGX (no cap)
Patient Pays: 1,200,000 - 960,000 = 240,000 UGX
```

---

## 🏗️ Code Structure

Each patient's data lives in a single dictionary (`d`) that is enriched by each function in turn as it moves through the pipeline.

| Function | Responsibility |
|---|---|
| `input_patient_details()` | Collects name, service type, duration (hours or days depending on type), insurance status, and provider |
| `validate_entry()` | Ensures no field is left blank; normalizes casing |
| `get_positive_integer()` | Ensures duration fields are valid non-negative integers |
| `validate_service_type()` | Ensures service type matches one of the four accepted categories |
| `validate_choices()` | Validates Yes/No responses (insurance status, add-another-patient) |
| `validate_insurance_provider()` | Case-insensitive lookup against accepted providers, normalized to a consistent display form |
| `determine_service_price()` | Computes the total service charge using the correct tiered logic for the patient's service type, recording a step-by-step breakdown as it goes |
| `calculate_insurance_coverage()` | Looks up the provider's rate and cap, applies the capped-coverage formula, and computes the patient's balance |
| `display_service_charge_breakdown()` | Prints the step-by-step pricing trace |
| `display_insurance_coverage()` | Prints the coverage calculation with provider-specific context |
| `display_patient_bill()` | Prints the final consolidated bill (with Minor/Major labeling for Surgery) |
| `display_daily_hospital_report()` | Aggregates totals, service-type breakdown, insurance statistics, and most common provider |
| `main()` | Orchestrates the loop: input → price → breakdown → coverage → bill → repeat/exit → report |

Both `determine_service_price()` and `calculate_insurance_coverage()` are table-driven where possible — `COVERAGE_TIERS` holds provider rate/cap data as a single lookup list, so adding a new insurer requires no change to the calculation logic itself.

---

## ▶️ How to Run

```bash
python3 hospital_patient_billing_system.py
```

You'll be prompted for patient and service details. After each entry, the service charge breakdown, insurance coverage, and final bill are displayed in sequence, then you're asked whether to add another patient. Answering **No** ends the session and prints the daily hospital report.

---

## 🖥️ Sample Session

```
Enter Patient Name: Alice Nambi
Enter Service Type (Consultation/Emergency/Surgery/Admission): Consultation
Enter Hours: 3
Insurance Status(Yes/No): Yes
Insurance Provider (NHIF/AAR/Jubilee/None): AAR

====================================================================================================
                                  SERVICE CHARGE BREAKDOWN
====================================================================================================
First hour          :         50,000 UGX
Additional 2 hour(s)   : 2 x 30000 = 60,000 UGX 
Total Service Charge     : 110,000 UGX

====================================================================================================
                                     INSURANCE COVERAGE
====================================================================================================
Provider          : AAR (80% coverage, no cap)
Coverage         : 88,000 UGX
Patient Pays: 110,000 - 88,000  = 22,000 UGX

====================================================================================================
                                        PATIENT BILL
====================================================================================================
Patient               : Alice Nambi
Service               : Consultation
Duration              : 3 hours
Total Service Charge  : 110,000 UGX
Insurance Coverage    : 88,000 UGX
Patient Pays          : 22,000 UGX

Add another patient? (Yes/No): No

====================================================================================================
                                     DAILY HOSPITAL REPORT
====================================================================================================
Total Patients Served:     1
Total Revenue Collected:   22,000 UGX
Average Bill Per Patient:  22,000 UGX
Sevice Breakdown:
Consultation  : 1
Surgery  : 0
Emergency  : 0
Admission  : 0
Insurance Statistics:
Yes :   1
No  :   0
 Most Common Provider(s): AAR
====================================================================================================
```

---

## ✅ Test Cases Verified

| Scenario | Service Charge | Insurance Coverage | Patient Pays |
|---|---|---|---|
| Consultation, 1 hour, No Insurance | 50,000 UGX | 0 UGX | 50,000 UGX |
| Admission, 10 days, NHIF | 1,230,000 UGX | 300,000 UGX (capped) | 930,000 UGX |
| Surgery, 4 hours, AAR (Major) | 1,200,000 UGX | 960,000 UGX | 240,000 UGX |

---

## 🧠 What This Assignment Reinforced

- Branching pricing logic that differs structurally per category, not just per lookup value
- Nested tiered calculations within a single service type (e.g. Admission's three day-range rates)
- Enforcing a maximum cap on a percentage-based calculation using `min()`
- Conditional field collection — prompting for `hours` vs `days` vs skipping the provider prompt entirely, based on earlier answers in the same input flow
- Recording a running list of calculation steps inside the data dictionary so the "show your working" display stays decoupled from the calculation logic itself
- Using `Counter` for categorical breakdowns and detecting ties in a "most common" result

---

## 📂 Repository Contents

```
├── Assignment_05_Hospital_Patient_Billing_System.pdf   # Original assignment brief
├── hospital_patient_billing_system.py                  # My solution
└── README.md                                            # This file
```

---

## 🧵 Series Note

This is part of an ongoing, sequential set of assignments from the **MIJ Technologies Python Programming Series**, each building on the last. Every solution in this repo series is written and understood by me before being committed — assignments are reviewed line-by-line for syntax and logic before upload.

**⬅️ Previous in series:** Assignment 04
**➡️ Next in series:** *Assignment 06 (coming soon)*
