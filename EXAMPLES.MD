# ═══════════════════════════════════════════
# Scientific Calculator — Written in Saral
# ═══════════════════════════════════════════

# ── Welcome ─────────────────────────────────
show "╔══════════════════════════════════════╗"
show "║   🔬  SARAL SCIENTIFIC CALCULATOR   ║"
show "║   Written entirely in Saral v2.0    ║"
show "╚══════════════════════════════════════╝"
show blank

# ── Menu function ────────────────────────────
define show_menu
    show "Choose an operation:"
    show blank
    show "  1.  Addition"
    show "  2.  Subtraction"
    show "  3.  Multiplication"
    show "  4.  Division"
    show "  5.  Power (a ^ b)"
    show "  6.  Square Root"
    show "  7.  Percentage"
    show "  8.  Remainder"
    show "  9.  Floor"
    show "  10. Ceiling"
    show "  11. Absolute Value"
    show "  12. Average of numbers"
    show "  13. Factorial"
    show "  14. Simple Interest"
    show "  15. Compound Interest"
    show "  16. Circle Area"
    show "  17. Triangle Area"
    show "  18. Pythagorean Theorem"
    show "  19. Temperature Converter"
    show "  20. Exit"
    show blank
end

# ── Factorial function ───────────────────────
define factorial using n
    store 1 in result
    count from 1 to n as i
        store result * i in result
    done
    return result
end

# ── Main calculator loop ─────────────────────
store "yes" in running

while running = "yes"
    call show_menu
    ask number "Enter your choice (1-20): " and store in choice
    show blank

    # ── Basic Operations ──────────────────────

    if choice = 1
        ask number "Enter first number: " and store in a
        ask number "Enter second number: " and store in b
        store a + b in result
        show "Result: " + result as text
    done

    if choice = 2
        ask number "Enter first number: " and store in a
        ask number "Enter second number: " and store in b
        store a - b in result
        show "Result: " + result as text
    done

    if choice = 3
        ask number "Enter first number: " and store in a
        ask number "Enter second number: " and store in b
        store a * b in result
        show "Result: " + result as text
    done

    if choice = 4
        ask number "Enter first number: " and store in a
        ask number "Enter second number (not zero): " and store in b
        if b = 0
            show "Error: Cannot divide by zero!"
        otherwise
            store a / b in result
            store round of result to 4 places in result
            show "Result: " + result as text
        done
    done

    if choice = 5
        ask number "Enter base number: " and store in a
        ask number "Enter power: " and store in b
        store a ^ b in result
        show "Result: " + result as text
    done

    # ── Scientific Operations ─────────────────

    if choice = 6
        ask number "Enter number: " and store in a
        if a < 0
            show "Error: Cannot take square root of negative number!"
        otherwise
            store sqrt of a in result
            store round of result to 6 places in result
            show "Square root: " + result as text
        done
    done

    if choice = 7
        ask number "Enter the number: " and store in a
        ask number "Enter percentage (%): " and store in b
        store a * b / 100 in result
        store round of result to 2 places in result
        show b as text + "% of " + a as text + " = " + result as text
    done

    if choice = 8
        ask number "Enter first number: " and store in a
        ask number "Enter second number: " and store in b
        store a % b in result
        show "Remainder: " + result as text
    done

    if choice = 9
        ask number "Enter number: " and store in a
        store floor of a in result
        show "Floor: " + result as text
    done

    if choice = 10
        ask number "Enter number: " and store in a
        store ceiling of a in result
        show "Ceiling: " + result as text
    done

    if choice = 11
        ask number "Enter number: " and store in a
        store absolute of a in result
        show "Absolute value: " + result as text
    done

    # ── Average ───────────────────────────────

    if choice = 12
        ask number "How many numbers? " and store in count
        make list called numbers
        count from 1 to count as i
            store i as text in i_text
            ask number "Enter number " + i_text + ": " and store in num
            add num to numbers
        done
        store sum of numbers in total
        store average of numbers in avg
        store round of avg to 4 places in avg
        show "Numbers entered: " + count as text
        show "Sum: " + total as text
        show "Average: " + avg as text
        store maximum of numbers in top
        store minimum of numbers in lowest
        show "Maximum: " + top as text
        show "Minimum: " + lowest as text
    done

    # ── Factorial ─────────────────────────────

    if choice = 13
        ask number "Enter a whole number (0-20): " and store in n
        if n < 0
            show "Error: Factorial not defined for negative numbers!"
        otherwise if n > 20
            show "Error: Number too large (max 20)!"
        otherwise
            store result of factorial with n in fact_result
            show n as text + "! = " + fact_result as text
        done
    done

    # ── Financial Calculations ────────────────

    if choice = 14
        show "── Simple Interest ─────────────────"
        show "Formula: SI = (Principal × Rate × Time) / 100"
        ask number "Enter Principal amount (₹): " and store in principal
        ask number "Enter Rate of interest (%): " and store in rate
        ask number "Enter Time (years): " and store in time
        store principal * rate * time / 100 in si
        store round of si to 2 places in si
        store principal + si in total_amount
        store round of total_amount to 2 places in total_amount
        show blank
        show "Principal:       ₹" + principal as text
        show "Rate:            " + rate as text + "%"
        show "Time:            " + time as text + " years"
        show "Simple Interest: ₹" + si as text
        show "Total Amount:    ₹" + total_amount as text
    done

    if choice = 15
        show "── Compound Interest ───────────────"
        show "Formula: A = P × (1 + R/100) ^ T"
        ask number "Enter Principal amount (₹): " and store in principal
        ask number "Enter Rate of interest (%): " and store in rate
        ask number "Enter Time (years): " and store in time
        store rate / 100 in rate_decimal
        store 1 + rate_decimal in base
        store base ^ time in multiplier
        store principal * multiplier in total_amount
        store round of total_amount to 2 places in total_amount
        store total_amount - principal in ci
        store round of ci to 2 places in ci
        show blank
        show "Principal:         ₹" + principal as text
        show "Rate:              " + rate as text + "%"
        show "Time:              " + time as text + " years"
        show "Compound Interest: ₹" + ci as text
        show "Total Amount:      ₹" + total_amount as text
    done

    # ── Geometry ──────────────────────────────

    if choice = 16
        show "── Circle Area & Circumference ─────"
        ask number "Enter radius: " and store in radius
        store 3.14159265 in pi
        store pi * radius * radius in area
        store 2 * pi * radius in circumference
        store round of area to 4 places in area
        store round of circumference to 4 places in circumference
        show "Radius:        " + radius as text
        show "Area:          " + area as text
        show "Circumference: " + circumference as text
    done

    if choice = 17
        show "── Triangle Area ───────────────────"
        ask number "Enter base: " and store in base
        ask number "Enter height: " and store in height
        store base * height / 2 in area
        store round of area to 4 places in area
        show "Base:   " + base as text
        show "Height: " + height as text
        show "Area:   " + area as text
    done

    if choice = 18
        show "── Pythagorean Theorem ─────────────"
        show "Find hypotenuse: c = sqrt(a² + b²)"
        ask number "Enter side a: " and store in a
        ask number "Enter side b: " and store in b
        store a ^ 2 in a_sq
        store b ^ 2 in b_sq
        store a_sq + b_sq in sum_sq
        store sqrt of sum_sq in hypotenuse
        store round of hypotenuse to 6 places in hypotenuse
        show "Side a:      " + a as text
        show "Side b:      " + b as text
        show "Hypotenuse:  " + hypotenuse as text
    done

    # ── Temperature Converter ─────────────────

    if choice = 19
        show "── Temperature Converter ───────────"
        show "  1. Celsius to Fahrenheit"
        show "  2. Fahrenheit to Celsius"
        show "  3. Celsius to Kelvin"
        ask number "Choose conversion (1-3): " and store in temp_choice
        ask number "Enter temperature: " and store in temp

        if temp_choice = 1
            store temp * 9 / 5 + 32 in converted
            store round of converted to 2 places in converted
            show temp as text + "°C = " + converted as text + "°F"
        done
        if temp_choice = 2
            store temp - 32 in step1
            store step1 * 5 / 9 in converted
            store round of converted to 2 places in converted
            show temp as text + "°F = " + converted as text + "°C"
        done
        if temp_choice = 3
            store temp + 273.15 in converted
            store round of converted to 2 places in converted
            show temp as text + "°C = " + converted as text + "K"
        done
    done

    # ── Exit ──────────────────────────────────

    if choice = 20
        show "Thank you for using Saral Scientific Calculator!"
        show "Goodbye! 👋"
        store "no" in running
    done

    # ── Invalid choice ────────────────────────
    if choice < 1
        show "Invalid choice. Please enter 1 to 20."
    done
    if choice > 20
        show "Invalid choice. Please enter 1 to 20."
    done

    if running = "yes"
        show blank
        show "────────────────────────────────────"
        show blank
    done

done
