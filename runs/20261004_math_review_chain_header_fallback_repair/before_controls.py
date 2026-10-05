from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import extract_mnu_limits as extractor


@pytest.mark.parametrize("suffix", [".txt", ".1.txt", ".2.txt"])
@pytest.mark.parametrize("sidecar", ["progress", "directory"])
def test_chain_readout_ignores_non_chain_candidates(tmp_path, suffix, sidecar):
    prefix = tmp_path / "posterior"
    Path(str(prefix) + suffix).write_text(
        "# weight minuslogpost mnu\n1 0 .1\n3 0 .4\n"
    )
    if sidecar == "progress":
        # This sorts before numbered chains and must not supply their header.
        Path(str(prefix) + ".0.progress.txt").write_text(
            "# iteration accepted elapsed\n999 8 123\n"
        )
    else:
        Path(str(prefix) + ".0.txt").mkdir()
    values, weights = extractor._load_chains_raw(prefix, "mnu", 0)[0]
    assert values.tolist() == [.1, .4]
    assert weights.tolist() == [1., 3.]
    assert extractor._weighted_quantile(values, weights, .95) == .4


def test_paramnames_do_not_make_numeric_directory_a_chain(tmp_path):
    prefix = tmp_path / "posterior"
    Path(str(prefix) + ".paramnames").write_text("mnu mass\n")
    Path(str(prefix) + ".txt").write_text("1 0 .1\n3 0 .4\n")
    Path(str(prefix) + ".0.txt").mkdir()
    values, weights = extractor._load_chains_raw(prefix, "mnu", 0)[0]
    assert extractor._weighted_quantile(values, weights, .95) == .4


def test_progress_file_alone_is_not_posterior_data(tmp_path):
    prefix = tmp_path / "posterior"
    Path(str(prefix) + ".progress.txt").write_text(
        "# weight minuslogpost mnu\n999 8 123\n"
    )
    with pytest.raises(FileNotFoundError, match="chain"):
        extractor._read_paramnames(prefix)


def test_numbered_families_keep_precedence_over_single_file(tmp_path):
    prefix = tmp_path / "posterior"
    Path(str(prefix) + ".txt").write_text(
        "# weight minuslogpost unrelated\n999 0 123\n"
    )
    for number, value in [(1, .1), (2, .4)]:
        Path(str(prefix) + f".{number}.txt").write_text(
            f"# weight minuslogpost mnu\n1 0 {value}\n"
        )
    families = extractor._load_chains_raw(prefix, "mnu", 0)
    assert [values.tolist() for values, weights in families] == [[.1], [.4]]
