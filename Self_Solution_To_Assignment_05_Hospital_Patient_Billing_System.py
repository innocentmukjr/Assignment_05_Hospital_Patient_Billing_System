'''
                            HOSPITAL PATIENT BILLING SYSTEM

WHAT THIS PROGRAM DOES
-----------------------
It pretends to be a hospital receptionist's terminal. The receptionist types
in a patient's visit details. The program:
  1. Works out a SERVICE CHARGE based on which of the four services the
     patient received (Consultation, Emergency, Surgery, Admission), using
     the pricing rules for that specific service.
  2. Works out how much of that charge INSURANCE covers (if the patient has
     insurance), respecting each provider's coverage percentage and, for
     some providers, a maximum cap in UGX.
  3. Prints a bill showing the charge, the insurance coverage, and what the
     patient personally has to pay.
  4. After every patient has been processed, prints a daily hospital report,
     including which service was most common and some insurance statistics.

HOW TO READ THIS FILE - PYTHON BASICS YOU NEED
------------------------------------------------
(These ideas repeat from the earlier assignment solutions - kept here too so
this file makes complete sense entirely on its own, without you needing to
flip back to an older file.)

- A CONSTANT (ALL_CAPS variable) is a fixed value set once at the top of the
  file - our lookup tables and formatting settings live here. Nothing below
  ever changes them; they are just referenced ("read").
- A TUPLE is a small, fixed group of values in round brackets, e.g.
  ('NHIF', 0.60, 300000) - one row of a lookup table. Tuples are perfect for
  "one row of related facts" because, unlike a list, you can't accidentally
  add or remove an item from them later.
- A LIST is a growable, ordered collection in square brackets. Used both for
  lookup tables (a list of tuples, i.e. many rows) and to collect every
  patient we've processed so far.
- A DICTIONARY holds "key: value" pairs, e.g. {'name': 'Alice', 'hours': 3}.
  We keep exactly ONE dictionary per patient, always called `d`, and every
  function below either reads facts out of it or adds new calculated facts
  into it. This means functions only ever need ONE argument (`d`) instead of
  many, and every function that runs later can see everything every earlier
  function already worked out - nothing gets lost or has to be re-passed
  around by hand.
- A FUNCTION (def name(...): ...) is a named, reusable block of code doing
  one job. Small, single-purpose functions keep each piece of logic easy to
  read, test, and fix in isolation, and they make main() read almost like a
  plain-English checklist of "what happens, in what order".
- A FOR LOOP repeats code once per item in a collection (e.g. once per tier
  in a pricing table). A WHILE LOOP repeats code for as long as a condition
  stays True - `while True:` repeats forever until something inside it
  explicitly stops it with a `break` or a `return`.
- A "HALF-OPEN INTERVAL" (lower, upper) means "lower is included, upper is
  NOT". We use this same convention as the previous parking assignment for
  every tiered pricing table below, e.g. (0, 2, 100000) means "hours 0 up
  to but not including 2" - i.e. the first two hours.
'''
from collections import Counter
# Counter is a ready-made tool from Python's standard library. Give it a
# list (or any iterable) of repeated items and it counts how many times
# each distinct item appears, e.g. Counter(['Car', 'Car', 'SUV']) produces
# {'Car': 2, 'SUV': 1}. We use this twice below: once to count how many
# patients used each SERVICE type, and once to count how many patients used
# each INSURANCE PROVIDER.


# ====================================================================
# CONSTANTS - our lookup tables, and formatting settings.
# ====================================================================

# The four service names, in the exact order we always want them displayed
# in (so the daily report's breakdown line is predictable, not shuffled).
SERVICE_TYPES = ['Consultation', 'Emergency', 'Surgery', 'Admission']

# A small dictionary that maps a SHOUTED version of each service name back
# to its correctly-cased display version, e.g. {'CONSULTATION':
# 'Consultation', 'EMERGENCY': 'Emergency', ...}. We use this to validate
# and "clean up" whatever casing the receptionist happens to type (e.g.
# "consultation", "CONSULTATION", or "Consultation" should all be accepted
# and all turn into the one correct spelling "Consultation").
# `{name.upper(): name for name in SERVICE_TYPES}` is a DICTIONARY
# COMPREHENSION - the dictionary version of a list comprehension. It loops
# over SERVICE_TYPES and, for every name in it, creates one entry:
# key = name.upper(), value = name (the original, correctly-cased spelling).
SERVICE_TYPE_LOOKUP = {name.upper(): name for name in SERVICE_TYPES}

# The four insurance providers a patient can have, in the exact order we
# always want them displayed in. 'None' here is a STRING (the four
# characters N-o-n-e) meaning "no insurance provider" - it is NOT Python's
# special `None` value. We use the string so it can sit inside f-strings
# and comparisons exactly like the other provider names, without needing
# special-case code every time we handle it.
INSURANCE_PROVIDERS = ['NHIF', 'AAR', 'Jubilee', 'None']
PROVIDER_LOOKUP = {name.upper(): name for name in INSURANCE_PROVIDERS}

VALID_INSURANCE_STATUS = {'Yes', 'No'}
# A SET works like a list but has no duplicates and lets Python check
# "is this value inside it?" very fast - perfect for validating input.

# Row format: (provider name, coverage fraction, maximum cap in UGX or None)
# A coverage fraction of 0.60 means "60% of the total bill". A cap of None
# means "no maximum - the full percentage always applies, however large the
# bill is". We store this as a LIST OF TUPLES (one tuple = one provider's
# full rule) and then turn it into a DICTIONARY below for fast lookups.
INSURANCE_INFO = [
    ('NHIF', 0.60, 300000),
    ('AAR', 0.80, None),
    ('Jubilee', 0.70, 500000),
    ('None', 0.00, None),
]

# `{provider: (pct, cap) for provider, pct, cap in INSURANCE_INFO}` is
# another dictionary comprehension. It loops over every tuple in
# INSURANCE_INFO, UNPACKS each tuple into three named pieces (provider,
# pct, cap - this works because each tuple has exactly three items, in
# that order), and builds a dictionary entry: key = provider name,
# value = a smaller (pct, cap) tuple. This turns our "list of rows" table
# into a fast "look up the details for one specific provider" table,
# e.g. INSURANCE_COVERAGE['NHIF'] instantly gives (0.60, 300000).
INSURANCE_COVERAGE = {provider: (pct, cap) for provider, pct, cap in INSURANCE_INFO}

# --- Service charge pricing tables ---
# Each of these is a list of (lower_bound, upper_bound, rate) tuples using
# the half-open interval convention explained at the top of this file.
# `rate` here means "UGX charged per hour/day that falls inside this tier"
# - NOT a multiplier like some other assignments use, so read it as
# "price per unit", e.g. 50000 means 50,000 UGX for every hour in that tier.

# Consultation: first hour costs 50,000 UGX flat. Every hour after that
# costs 30,000 UGX. Writing "first hour" as the half-open interval (0, 1)
# with rate 50000 achieves exactly this: it can only ever contain 1 hour.
CONSULTATION_TIERS = [
    (0, 1, 50000),                # hour 1 (the very first hour only)
    (1, float('inf'), 30000),     # every hour after that, with no upper limit
]

# Emergency: first 2 hours cost 100,000 UGX/hour. Every hour after that
# costs 80,000 UGX/hour.
EMERGENCY_TIERS = [
    (0, 2, 100000),                # the first 2 hours
    (2, float('inf'), 80000),      # every hour after that
]

# Admission: days 1-3 cost 150,000 UGX/day, days 4-7 cost 120,000 UGX/day,
# and every day beyond that costs 100,000 UGX/day. Note the half-open
# convention again: (0, 3, ...) means "day count 0 up to but not including
# 3", i.e. days 1, 2, and 3 - THREE days total, which matches "Days 1-3".
ADMISSION_TIERS = [
    (0, 3, 150000),                 # days 1-3   (3 days)
    (3, 7, 120000),                 # days 4-7   (4 days)
    (7, float('inf'), 100000),      # day 8 onward, no upper limit
]

# Surgery does NOT use a tiered table at all - it's a single flat fee that
# depends only on whether the duration crosses a 3-hour threshold, so no
# constant table is needed for it; the two flat amounts are just written
# directly inside calculate_service_charge() further down.

# --- output formatting settings ---
# Rather than typing a long row of "=" characters by hand into every single
# print() statement (easy to mistype, and easy to end up with lines that
# are all slightly different lengths), we build the separator line ONCE
# here with string multiplication: '=' * 79 produces a string that repeats
# '=' seventy-nine times in a row. Changing the one LINE_WIDTH number
# resizes every separator and every centered title in the whole program.
LINE_WIDTH = 79
SEPARATOR = '=' * LINE_WIDTH

# How many characters wide we reserve for the "label" part of every
# "Label : value" line printed below, so the colons all line up neatly no
# matter how long each individual label text is.
LABEL_WIDTH = 26


def print_boxed_header(title):
    """
    Print a top separator line, the given title CENTERED within the same
    width, then a bottom separator line - a uniform "boxed" section header
    no matter how long or short the title text is.

    str.center(width) pads a string with spaces on both the left and right
    sides until the total length equals `width`, keeping the original text
    in the middle, e.g. "HELLO".center(11) -> "  HELLO    ".
    """
    print(SEPARATOR)
    print(title.center(LINE_WIDTH))
    print(SEPARATOR)


def print_line(label, value):
    """
    Print one line of a bill/report in a consistent
    " Label                    : value" layout.

    f"{label:<{LABEL_WIDTH}}" is an f-string FORMAT SPEC: `<` means
    "left-align this text", and `{LABEL_WIDTH}` inside the spec plugs in our
    LABEL_WIDTH constant as the field width, padding the label with spaces
    on the right until it's exactly LABEL_WIDTH characters wide - so every
    colon lands in the same column, whether the label is short ("Coverage")
    or long ("Average Bill Per Patient").
    """
    print(f" {label:<{LABEL_WIDTH}}: {value}")


# ====================================================================
# INPUT / VALIDATION
#
# Every function below follows the same pattern: "keep asking until the
# answer is valid."
# ====================================================================

def get_nonempty_text(prompt):
    """
    The most basic building block: ask for a line of text and refuse to
    accept an empty answer. This does NOT apply any letter-casing - it
    hands back exactly what the user typed (just trimmed of stray
    leading/trailing spaces). We need this "raw" version separately because
    several fields below (service type, insurance status, insurance
    provider) each need to apply THEIR OWN casing/validation rules on top
    of this basic "not empty" check.
    """
    while True:
        entry = input(prompt)
        if entry.strip():
            # .strip() removes leading/trailing spaces. A non-empty string
            # counts as "truthy" in an if-check, so this reads as "if
            # something is actually left after trimming spaces."
            return entry.strip()
        print('Field cannot be empty, please try again...')


def validate_entry(prompt):
    """
    Ask for a line of text, refuse an empty answer, and tidy it up with
    .title() - which capitalises the first letter of every word, e.g.
    "john smith" -> "John Smith". This is what we use for ordinary text
    fields (the patient's name) and for the final yes/no "add another
    patient?" question, where we only ever check for the exact word "No".
    """
    while True:
        entry = get_nonempty_text(prompt)
        return entry.title()


def validate_service_type(prompt):
    """
    Ask for a service type and keep asking until it matches one of the four
    valid services, in ANY casing the receptionist happens to type.

    raw.upper() turns whatever was typed into SHOUTING CASE, e.g.
    "consultation" -> "CONSULTATION". We then look that shouted version up
    in SERVICE_TYPE_LOOKUP. If it's a key in that dictionary, we get back
    the correctly-cased official name; if it ISN'T a key at all, dict.get()
    safely returns None (its second, optional argument would be a
    fallback value - we don't give one, so the default fallback is None)
    instead of crashing the program with an error.
    """
    while True:
        raw = get_nonempty_text(prompt)
        normalized = SERVICE_TYPE_LOOKUP.get(raw.upper())
        if normalized is not None:
            return normalized
        print(f"Please enter one of: {', '.join(SERVICE_TYPES)}")
        # ', '.join(SERVICE_TYPES) glues every item in the list together
        # into one string, separated by ", " - turning
        # ['Consultation', 'Emergency', 'Surgery', 'Admission'] into
        # "Consultation, Emergency, Surgery, Admission".


def validate_insurance_status(prompt):
    """
    Ask "Yes" or "No" (in any casing) and keep asking until we get exactly
    one of those two words.
    """
    while True:
        raw = get_nonempty_text(prompt)
        candidate = raw.title()   # "yes" / "YES" / "Yes" all become "Yes"
        if candidate in VALID_INSURANCE_STATUS:
            return candidate
        print("Please enter 'Yes' or 'No'.")


def validate_insurance_provider(prompt, insurance_status):
    """
    Ask for an insurance provider and enforce the ONE special rule the
    assignment brief calls out explicitly: the provider and the insurance
    status must AGREE with each other.
        - If insurance_status is 'No', the provider MUST be 'None'.
        - If insurance_status is 'Yes', the provider must be a REAL
          provider (NHIF, AAR, or Jubilee) - it can't be 'None'.

    Notice this function takes a SECOND argument, insurance_status, on top
    of the usual prompt - it needs to know the earlier answer in order to
    correctly judge whether THIS answer is allowed. This is exactly why we
    build up one shared dictionary `d` field-by-field elsewhere: later
    answers often depend on earlier ones.
    """
    while True:
        raw = get_nonempty_text(prompt)
        normalized = PROVIDER_LOOKUP.get(raw.upper())
        if normalized is None:
            print(f"Please enter one of: {', '.join(INSURANCE_PROVIDERS)}")
            continue
            # `continue` immediately jumps back to the top of the while
            # loop, skipping every line below it - so none of the
            # insurance_status checks further down even run for an
            # already-invalid provider name.
        if insurance_status == 'No' and normalized != 'None':
            print("Insurance Status is 'No', so Provider must be 'None'.")
            continue
        if insurance_status == 'Yes' and normalized == 'None':
            print("Insurance Status is 'Yes', so Provider cannot be 'None'. "
                  "Please choose NHIF, AAR, or Jubilee.")
            continue
        return normalized


def get_positive_integer(prompt):
    """
    Ask for a whole number and keep asking until it's actually a valid,
    positive whole number.

    int(raw) tries to convert the typed text into an integer. If the text
    isn't a valid whole number at all (e.g. "abc", or "3.5", or an empty
    string), Python raises a ValueError - an error/exception object -
    instead of crashing the whole program immediately. The try/except
    block below "catches" that specific error so we can print a friendly
    message and ask again instead.
    """
    while True:
        raw = input(prompt)
        try:
            value = int(raw)
        except ValueError:
            print('Please enter a whole number.')
            continue
        if value <= 0:
            print('Please enter a number greater than 0.')
            continue
        return value


# ====================================================================
# PART A - PATIENT INFORMATION INPUT
# ====================================================================

def patient_entry_input():
    """
    Ask every question for ONE patient visit, in order, and return a fresh
    dictionary holding all the raw answers. Every function further down
    the file will keep adding MORE keys into this same dictionary as it
    works out charges, coverage, and totals - but this function is only
    responsible for the five raw facts the receptionist actually typed in.
    """
    d = {}
    # `d = {}` creates a brand new, empty dictionary. We build it up one
    # key at a time below using square-bracket assignment, e.g.
    # d['name'] = ... creates (or overwrites) the 'name' key in `d`.

    d['name'] = validate_entry('Enter Patient Name: ')

    d['service_type'] = validate_service_type(
        'Enter Service Type (Consultation/Emergency/Surgery/Admission): '
    )

    # Admission is measured in DAYS; every other service is measured in
    # HOURS. We ask the right question, and remember which unit word
    # ('day' or 'hour') applies, so every later display function can print
    # the correct word without needing to re-check the service type itself.
    if d['service_type'] == 'Admission':
        d['duration'] = get_positive_integer('Enter Number of Days: ')
        d['duration_unit'] = 'day'
    else:
        d['duration'] = get_positive_integer('Enter Hours: ')
        d['duration_unit'] = 'hour'

    d['insurance_status'] = validate_insurance_status('Insurance Status (Yes/No): ')

    d['insurance_provider'] = validate_insurance_provider(
        'Insurance Provider (NHIF/AAR/Jubilee/None): ',
        d['insurance_status'],
        # We pass in d['insurance_status'] - the answer we JUST stored a
        # couple of lines above - so validate_insurance_provider() can
        # enforce the "status and provider must agree" rule explained in
        # that function's own docstring.
    )

    return d


# ====================================================================
# PARTS B & C - SERVICE PRICING AND TIERED CHARGE CALCULATION
# ====================================================================

def calculate_tiered_charge(duration, tiers):
    """
    A REUSABLE calculator shared by Consultation, Emergency, and Admission,
    since all three follow the exact same PATTERN: "spend down a duration,
    tier by tier, charging a different rate once you cross each boundary."
    Only Surgery is different (a flat fee, not tiered), so it does NOT use
    this function - see calculate_service_charge() below.

    Parameters
    ----------
    duration : int
        The total number of hours (or days, for Admission) the patient
        used, e.g. 7.
    tiers : list of (lower_bound, upper_bound, rate) tuples
        One of CONSULTATION_TIERS / EMERGENCY_TIERS / ADMISSION_TIERS from
        the constants section above, using the half-open interval
        convention: `upper_bound` is NOT included in that tier.

    Returns
    -------
    (total, breakdown) - a TUPLE containing two things at once:
        total : the full charge in UGX, as a plain number.
        breakdown : a list of (units_used, rate, subtotal) tuples, one
            entry per tier that actually got used, in order. Only tiers
            the patient's duration actually reached appear here - e.g. a
            2-hour Emergency visit produces only ONE breakdown entry,
            because the second tier (hours beyond 2) was never touched.

    HOW THE MATH WORKS
    -------------------
    We track `remaining` - how much duration is still left to "spend" -
    starting equal to the full duration. We walk through the tiers in
    order. For each tier, we work out its CAPACITY (how many hours/days
    that tier can possibly absorb: upper_bound - lower_bound), then charge
    for whichever is SMALLER: the tier's capacity, or however much
    duration we still have left. Whatever we charge for gets subtracted
    from `remaining`, and we move on to the next tier. Once `remaining`
    reaches 0, we stop early - there's nothing left to charge for.
    """
    remaining = duration
    total = 0
    breakdown = []
    # `breakdown = []` starts as an empty list; we'll .append() one tuple
    # to it per tier used, building it up as the loop runs.

    for (lower, upper, rate) in tiers:
        # `for (lower, upper, rate) in tiers:` loops over the list of
        # tuples and UNPACKS each 3-item tuple into three separate names
        # in one step, exactly like the dictionary comprehension near the
        # top of this file did with INSURANCE_INFO.

        if remaining <= 0:
            break
            # Nothing left to charge for - stop looking at further tiers
            # entirely. `break` immediately exits the for loop.

        tier_capacity = upper - lower
        # How many hours/days this tier is ABLE to hold, e.g. for
        # (0, 2, 100000), tier_capacity = 2 - 0 = 2 hours. For a tier whose
        # upper bound is float('inf'), this becomes infinity minus a
        # normal number, which Python happily calculates as still
        # infinity - meaning "this tier has no ceiling."

        units_in_tier = min(remaining, tier_capacity)
        # min() returns whichever of its arguments is smaller. We can
        # never charge for MORE than what's left (`remaining`), and we can
        # never charge for more than the tier physically holds
        # (`tier_capacity`) - so the smaller of the two is exactly right.

        if units_in_tier <= 0:
            continue
            # This tier hasn't been reached at all (can happen if an
            # earlier tier already absorbed everything) - skip straight to
            # checking the next tier, without adding anything to
            # `breakdown`.

        subtotal = units_in_tier * rate
        breakdown.append((units_in_tier, rate, subtotal))
        total += subtotal
        remaining -= units_in_tier
        # `remaining -= units_in_tier` is shorthand for
        # `remaining = remaining - units_in_tier` - we've now "spent" that
        # many hours/days, so there's less left for the next tier.

    return total, breakdown


def calculate_service_charge(d):
    """
    Work out d['total_charge'] (and, for the three tiered services,
    d['charge_breakdown']) using whichever pricing rule matches
    d['service_type']. This is the "traffic director" function: it doesn't
    do any pricing math itself - it just picks the right tool for the job
    and stores the result(s) back into `d`.
    """
    service = d['service_type']

    if service == 'Consultation':
        total, breakdown = calculate_tiered_charge(d['duration'], CONSULTATION_TIERS)
        d['total_charge'] = total
        d['charge_breakdown'] = breakdown

    elif service == 'Emergency':
        total, breakdown = calculate_tiered_charge(d['duration'], EMERGENCY_TIERS)
        d['total_charge'] = total
        d['charge_breakdown'] = breakdown

    elif service == 'Admission':
        total, breakdown = calculate_tiered_charge(d['duration'], ADMISSION_TIERS)
        d['total_charge'] = total
        d['charge_breakdown'] = breakdown

    else:
        # The only remaining possibility, since validate_service_type()
        # only ever hands back one of the four SERVICE_TYPES, is 'Surgery'.
        # Surgery is a FLAT fee decided purely by which side of the
        # 3-hour line the duration falls on - there's no tier list, so we
        # calculate it directly here instead of calling
        # calculate_tiered_charge().
        if d['duration'] < 3:
            d['surgery_category'] = 'Minor'
            d['total_charge'] = 500000
        else:
            d['surgery_category'] = 'Major'
            d['total_charge'] = 1200000


# ====================================================================
# PART C (continued) - INSURANCE COVERAGE CALCULATION
# ====================================================================

def calculate_insurance_coverage(d):
    """
    Work out how much of d['total_charge'] the patient's insurance covers,
    and how much the patient personally has to pay - then store both
    numbers (plus a couple of extra details needed for display) into `d`.

    THE INSURANCE FORMULA
    ----------------------
        Insurance Coverage = min(Total Bill x Coverage %, Maximum Cap)
        Patient Pays        = Total Bill - Insurance Coverage

    If a provider has NO cap (like AAR), we simply skip the min() step and
    apply the full percentage, however large the bill is.
    """
    provider = d['insurance_provider']
    coverage_pct, cap = INSURANCE_COVERAGE[provider]
    # This is DICTIONARY UNPACKING again: INSURANCE_COVERAGE[provider]
    # looks up the (pct, cap) tuple we built for this exact provider back
    # in the constants section, and the two names on the left
    # (coverage_pct, cap) immediately receive the tuple's two items.

    total = d['total_charge']
    raw_coverage = total * coverage_pct
    # "raw" because this is BEFORE the cap is applied - we keep this
    # number around separately so the display function below can show
    # both the uncapped calculation AND the fact that it got capped, e.g.
    # "738,000 -> CAPPED at 300,000".

    if cap is not None:
        coverage = min(raw_coverage, cap)
        # min() again: the patient's insurer will never pay out MORE than
        # its cap, so we take whichever is smaller.
    else:
        coverage = raw_coverage

    patient_pays = total - coverage

    d['coverage_pct'] = coverage_pct
    d['cap'] = cap
    d['raw_coverage'] = raw_coverage
    d['coverage_amount'] = coverage
    d['patient_pays'] = patient_pays


# ====================================================================
# PART D - PATIENT BILL DISPLAY
# ====================================================================

def display_charge_breakdown(d):
    """
    Show exactly how the service charge was built up, tier by tier (or, for
    Surgery, show which flat-rate category applied and why).
    """
    print()
    print_boxed_header('SERVICE CHARGE BREAKDOWN')

    service = d['service_type']

    if service == 'Surgery':
        if d['surgery_category'] == 'Minor':
            print(' Duration < 3 hrs -> Minor Surgery (flat rate)')
        else:
            print(' Duration >= 3 hrs -> Major Surgery (flat rate)')
        print_line('Service Charge', f"{d['total_charge']:,.0f} UGX")
        # `return` here ends the function immediately - Surgery has no
        # tiers to loop over, so none of the code below this point (which
        # only makes sense for tiered services) should run for it.
        return

    unit_word = d['duration_unit']   # either 'hour' or 'day'

    if service == 'Admission':
        # Admission gets its own DAY-RANGE labels ("Days 1-3", "Days 4-7",
        # ...) to match the exact wording the assignment brief uses. We
        # rebuild those ranges here by walking the breakdown list and
        # keeping a running "which day are we currently on" counter.
        day_start = 1
        for units, rate, subtotal in d['charge_breakdown']:
            day_end = day_start + units - 1
            if units == 1:
                label = f"Day {day_start}"
            else:
                label = f"Days {day_start}-{day_end}"
            print_line(label, f"{units} x {rate:,.0f} = {subtotal:,.0f} UGX")
            day_start = day_end + 1
            # Move the counter forward by however many days this tier just
            # used up, so the NEXT tier's range starts right after it.

    else:
        # Consultation and Emergency both use HOUR-based "First .../
        # Additional ..." labels instead of day ranges.
        #
        # `enumerate(d['charge_breakdown'])` walks the list while also
        # handing us each item's position (0, 1, 2, ...) as `index`, so we
        # can tell "is this the very first tier used?" without a separate
        # counter variable.
        for index, (units, rate, subtotal) in enumerate(d['charge_breakdown']):
            plural = '' if units == 1 else 's'
            # 1 hour -> "hour", 2 hours -> "hours". Same idea as `plural`
            # anywhere else you've seen singular/plural text handled.

            if index == 0 and units == 1:
                # Special case matching the assignment's own sample
                # output: a first tier of exactly one unit (e.g.
                # Consultation's first hour) is shown as a plain amount,
                # with no "1 x rate =" multiplication shown, since
                # multiplying by 1 doesn't teach us anything extra.
                print_line(f"First {unit_word}", f"{subtotal:,.0f} UGX")
                continue

            if index == 0:
                label = f"First {units} {unit_word}{plural}"
            else:
                label = f"Additional {units} {unit_word}{plural}"
            print_line(label, f"{units} x {rate:,.0f} = {subtotal:,.0f} UGX")

    print_line('Total Service Charge', f"{d['total_charge']:,.0f} UGX")


def display_insurance_coverage(d):
    """
    Show the insurance calculation: which provider, what percentage and
    cap applied, and the exact arithmetic that produced the coverage
    amount and the patient's final out-of-pocket amount.
    """
    print()
    print_boxed_header('INSURANCE COVERAGE')

    provider = d['insurance_provider']

    if provider == 'None':
        # No insurance at all - the patient pays the full charge, and
        # there's no percentage/cap arithmetic worth showing.
        print_line('Provider', 'None (0% coverage)')
        print_line('Coverage', '0 UGX')
        print_line('Patient Pays', f"{d['patient_pays']:,.0f} UGX")
        return

    pct = d['coverage_pct']
    cap = d['cap']

    cap_text = f"{cap:,.0f} UGX cap" if cap is not None else "no cap"
    # This is a CONDITIONAL EXPRESSION (a compact one-line if/else that
    # produces a VALUE instead of running a whole statement block). Read
    # it right-to-left: "if cap is not None, use the first text, otherwise
    # use the second text."
    print_line('Provider', f"{provider} ({pct * 100:.0f}% coverage, {cap_text})")

    coverage_line = f"{d['total_charge']:,.0f} x {pct:.2f} = {d['raw_coverage']:,.0f} UGX"
    if cap is not None and d['raw_coverage'] > cap:
        coverage_line += f" -> CAPPED at {cap:,.0f} UGX"
        # `+=` here means "stick this extra text onto the end of the
        # string we already built" - it only happens when the uncapped
        # coverage actually exceeded the cap, so an AAR patient (no cap at
        # all) or a small NHIF bill under the cap never see this extra
        # note.
    print_line('Coverage', coverage_line)

    print_line(
        'Patient Pays',
        f"{d['total_charge']:,.0f} - {d['coverage_amount']:,.0f} = {d['patient_pays']:,.0f} UGX",
    )


def display_patient_bill(d):
    """
    Print the final, summarised bill. By the time this runs, `d` has
    passed through every function above, picking up new keys along the
    way: name/service_type/duration/duration_unit/insurance_status/
    insurance_provider -> total_charge (and charge_breakdown, or
    surgery_category) -> coverage_pct/cap/raw_coverage/coverage_amount/
    patient_pays. That's the whole point of using one dictionary the
    entire way through - every downstream function can see everything
    earlier functions worked out, without us ever passing around a
    handful of loose variables.
    """
    print()
    print_boxed_header('PATIENT BILL')

    print_line('Patient', d['name'])

    if d['service_type'] == 'Surgery':
        service_display = f"Surgery ({d['surgery_category']})"
    else:
        service_display = d['service_type']
    print_line('Service', service_display)

    plural = '' if d['duration'] == 1 else 's'
    print_line('Duration', f"{d['duration']} {d['duration_unit']}{plural}")

    print_line('Total Service Charge', f"{d['total_charge']:,.0f} UGX")
    print_line('Insurance Coverage', f"{d['coverage_amount']:,.0f} UGX")
    print_line('Patient Pays', f"{d['patient_pays']:,.0f} UGX")


# ====================================================================
# PART E - DAILY HOSPITAL REPORT
#
# `patients` is a plain list holding one finished patient dictionary per
# patient processed, e.g.:
#   patients = [
#       {'name': 'Alice Nambi', 'service_type': 'Consultation',
#        'patient_pays': 22000, 'insurance_provider': 'AAR', ...},
#       {'name': 'John Okello', 'service_type': 'Surgery',
#        'patient_pays': 500000, 'insurance_provider': 'None', ...},
#   ]
# Every statistic below is worked out by scanning this list.
# ====================================================================

def display_daily_report(patients):
    print()
    print_boxed_header('DAILY HOSPITAL REPORT')

    if not patients:
        # An empty list is "falsy" in an if-check, so `not patients` reads
        # as "if the patients list has nothing in it."
        print_line('Status', 'No patients were served today.')
        return

    total_patients = len(patients)
    # len() returns how many items are in the list.

    total_revenue = sum(p['patient_pays'] for p in patients)
    # `sum(p['patient_pays'] for p in patients)` is a GENERATOR EXPRESSION
    # inside sum(). It visits every patient dictionary in the list, in
    # turn, pulls out just its 'patient_pays' value, and sum() adds all of
    # those values together into one running total. We deliberately sum
    # patient_pays (what the HOSPITAL actually collects from patients),
    # not total_charge, since insurance-covered amounts aren't "revenue
    # collected from the patient".

    average_bill = total_revenue / total_patients

    service_counts = Counter(p['service_type'] for p in patients)
    # Counts how many patients used each service today, e.g.
    # {'Consultation': 1, 'Surgery': 1} if one of each was seen.

    service_breakdown = ' | '.join(
        f"{service}: {service_counts.get(service, 0)}" for service in SERVICE_TYPES
    )
    # service_counts.get(service, 0) means "look up this service's count,
    # or use 0 if that service was never seen at all today" - so, e.g.,
    # "Emergency: 0" still prints instead of Emergency vanishing from the
    # line entirely.

    highest_service_count = max(service_counts.values())
    # service_counts.values() gives just the counts (ignoring which
    # service they belong to); max() finds the single largest one.

    most_common_services = [
        service for service in SERVICE_TYPES
        if service_counts.get(service, 0) == highest_service_count
    ]
    # This is a LIST COMPREHENSION with a condition attached. It walks
    # SERVICE_TYPES (so results always come out in a consistent
    # Consultation/Emergency/Surgery/Admission order) and keeps only the
    # services whose count matches highest_service_count. If exactly one
    # service has the highest count, this list ends up with just that one
    # name. If TWO OR MORE services are TIED for the highest count, ALL of
    # them end up in this list - which is exactly how we correctly handle
    # ties instead of just picking whichever one happened to come first.

    most_common_service_str = ' / '.join(most_common_services)
    if len(most_common_services) > 1:
        most_common_service_str += ' (Tie)'

    with_insurance = sum(1 for p in patients if p['insurance_status'] == 'Yes')
    # `sum(1 for p in patients if ...)` is another generator expression:
    # it produces the number 1 for every patient that matches the
    # condition, and 0 contributions for every patient that doesn't (since
    # non-matching patients are skipped entirely by the `if`), so summing
    # them counts exactly how many patients matched. This is a very common
    # Python pattern for "count how many items satisfy a condition."
    without_insurance = total_patients - with_insurance

    # For "most common provider", we only care about patients who actually
    # HAVE insurance - a patient with provider 'None' shouldn't count
    # towards any real provider's total.
    provider_counts = Counter(
        p['insurance_provider'] for p in patients if p['insurance_provider'] != 'None'
    )

    if provider_counts:
        # A Counter with at least one entry in it is "truthy"; an empty
        # one (nobody had insurance today) is "falsy" - so this reads as
        # "only do this if at least one patient had real insurance."
        highest_provider_count = max(provider_counts.values())
        most_common_providers = [
            provider for provider in INSURANCE_PROVIDERS
            if provider != 'None' and provider_counts.get(provider, 0) == highest_provider_count
        ]
        most_common_provider_str = ' / '.join(most_common_providers)
        if len(most_common_providers) > 1:
            most_common_provider_str += ' (Tie)'
    else:
        most_common_provider_str = 'None'

    print_line('Total Patients Served', total_patients)
    print_line('Total Revenue Collected', f"{total_revenue:,.0f} UGX")
    print_line('Average Bill Per Patient', f"{average_bill:,.0f} UGX")
    print_line('Service Breakdown', service_breakdown)
    print_line('Most Common Service', most_common_service_str)
    print_line('Insurance Statistics', f"With Insurance: {with_insurance} | Without: {without_insurance}")
    print_line('Most Common Provider', most_common_provider_str)


# ====================================================================
# MAIN
#
# This is the "control centre": it calls every function above, in the
# right order, once per patient, until the receptionist chooses to stop.
# Reading just this function top-to-bottom should tell you the whole story
# of the program, even without looking at any other function's internals.
# ====================================================================

def main():
    print_boxed_header('HOSPITAL PATIENT BILLING SYSTEM v1.0')

    patients = []
    # An empty list that will grow by one dictionary per patient we
    # process. We keep this as its own plain, independent variable that
    # main() is directly responsible for - it isn't nested inside anything
    # else, and there's no separate counter needed for this assignment
    # since no visit numbers are required.

    while True:
        # `while True:` repeats forever - the ONLY way out is the `break`
        # statement further down, which only runs once the receptionist
        # answers "no" to "Add another patient?".

        d = patient_entry_input()
        # ask for name/service_type/duration/duration_unit/
        # insurance_status/insurance_provider; d is now a fresh dictionary
        # holding those six facts about this one patient visit.

        calculate_service_charge(d)     # adds 'total_charge' (and 'charge_breakdown' or 'surgery_category') to d
        calculate_insurance_coverage(d)  # adds 'coverage_pct', 'cap', 'raw_coverage', 'coverage_amount', 'patient_pays' to d

        display_charge_breakdown(d)
        display_insurance_coverage(d)
        display_patient_bill(d)

        patients.append(d)
        # save this finished patient's whole dictionary into our running
        # list, so display_daily_report can use it later.

        again = validate_entry('Add another patient? (yes/no): ')
        if again == 'No':
            break
            # `break` immediately exits the while loop - no more patients
            # will be processed today.
        # if the receptionist typed anything other than exactly "No"
        # (including "Yes"), we simply fall through here and the while
        # loop goes straight back to the top to process another patient.

    display_daily_report(patients)
    # only runs once the while loop has actually ended.


# This special check means: "only actually run main() if this file is being
# executed directly (e.g. by typing
# `python hospital_patient_billing_system.py` in a terminal), not if some
# OTHER file imports this one to reuse its functions." It's a standard
# convention in almost every Python program.
if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        # EOFError/KeyboardInterrupt happen if the input stream closes
        # unexpectedly or the user presses Ctrl+C - we exit quietly with a
        # friendly message instead of showing a scary error trace.
        print('\nProgram interrupted by User, Closing....')
    except Exception as e:
        # A catch-all safety net: if ANYTHING unexpected goes wrong
        # anywhere in the program that we didn't specifically plan for,
        # print a short, friendly message using the error's own text (e)
        # instead of letting the whole program crash with a wall of
        # technical error output.
        print(f"An Unexpected Error ({e}) Occured, Program closing...")
