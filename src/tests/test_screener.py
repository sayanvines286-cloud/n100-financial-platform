from src.screener.engine import apply_filters, presets, financial_ratios, cagr, cashflow


def get_test_dataframe():
    df = (
        financial_ratios
        .merge(cagr, on="company_id", how="left")
        .merge(cashflow, on=["company_id", "year"], how="left")
    )
    return df


def test_all_presets_exist():
    expected_presets = {
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_bluechip",
        "turnaround_watch",
    }

    assert expected_presets.issubset(set(presets.keys()))


def test_all_presets_run():
    df = get_test_dataframe()

    for name, preset in presets.items():
        result = apply_filters(df, preset)

        assert result is not None
        assert len(result) <= len(df)


def test_presets_return_expected_results():
    df = get_test_dataframe()

    expected_minimum_rows = {
        "quality_compounder": 1,
        "value_pick": 1,
        "growth_accelerator": 1,
        "dividend_champion": 1,
        "debt_free_bluechip": 1,
        "turnaround_watch": 1,
    }

    for name, minimum_rows in expected_minimum_rows.items():
        result = apply_filters(df, presets[name])

        assert len(result) >= minimum_rows, (
            f"{name} returned {len(result)} rows"
        )


def test_screener_columns_are_preserved():
    df = get_test_dataframe()
    result = apply_filters(df, presets["quality_compounder"])

    assert "company_id" in result.columns
    assert "year" in result.columns