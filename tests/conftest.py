def pytest_addoption(parser):
    parser.addoption(
        "--e2e-base",
        default="main",
        help="e2e: the pushed branch the Demo PRs are based on, i.e. the branch under test",
    )
