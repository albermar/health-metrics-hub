* Output metrics (KPIs):
    1. — Energy Balance (5 KPIs)
        - basal_spend = 
            - for male: 66.47 + 13.75 * weight_kg + 5.00 * height_cm - 6.76 * age_years
            - for female: 655.10 + 9.56 * weight_kg + 1.85 * height_cm - 4.68 * age_years
        - NEAT_from_steps = 0.0005 * weight_kg * steps_n
        - kcal_out_total = basal_spend + NEAT_from_steps + kcal_out_training
        - balance_kcal = kcal_out_total - kcal_in
        - balance_7d_average = mean_last_7(balance_kcal)

    2. — Nutrition (3 KPIs)
        - protein_per_kg = proteins_g / weight_kg
        - protein_pct = (proteins_g * 4) / kcal_in
        - healthy_food_pct = (kcal_in - kcal_junk_in) / kcal_in

    3. — Activity (3 KPIs)
        - adherence_steps = 1 if steps_n >= steps_goal else 0
        - steps_7d_avg = mean_last_7(steps_n)
        - steps_slope = slope_last_14(steps_n)

    4. — Physiology (4 KPIs)
        - weight_7d_avg = mean_last_7(weight_kg)
        - weight_slope = slope_last_14(weight_kg)
        - kg_fat_loss = sum_last_n(balance_kcal) / 7700
        - waist_change_7d = waist_cm(today) - waist_cm(7_days_ago)

    5. — Recovery (2 KPIs)
        - sleep_7d_avg = mean_last_7(sleep_hours)
        - stress_7d_avg = mean_last_7(stress_rel)

