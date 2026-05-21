import numpy as np
import pandas as pd

from huff_curves_br.pipeline import PipelineConfig, run_pipeline


def test_pipeline_writes_station_event_and_curve_tables(tmp_path):
    stations = tmp_path / "stations.csv"
    stations.write_text("Codigo,Lat,Lon,Area\n123,-15.0,-47.0,10\n", encoding="utf-8")

    def downloader(station_id, start, end, config):
        times = pd.date_range("2020-01-01", periods=120, freq="15min")
        rain = np.zeros(len(times), dtype=float)
        rain[1:7] = [2, 2, 1, 1, 0.5, 0.5]
        rain[70:76] = [0.5, 1, 2, 2, 1, 0.5]
        return pd.DataFrame({"station_id": station_id, "datetime": times, "rainfall_mm": rain})

    config = PipelineConfig(
        station_catalog_path=stations,
        raw_dir=tmp_path / "raw",
        output_dir=tmp_path / "outputs",
        min_years=0,
        max_missing_fraction=1,
        min_event_depth_mm=0.1,
        min_event_records=1,
    )

    outputs = run_pipeline(config, downloader=downloader)

    assert outputs.station_results_path.exists()
    assert outputs.event_table_path.exists()
    assert outputs.curve_table_path.exists()
    assert outputs.station_results.loc[0, "status"] == "ok"
    assert outputs.station_results.loc[0, "n_events"] == 2
    assert len(outputs.event_table) == 2
    assert not outputs.curve_table.empty
