# Comprehensive OCR Test Case Report

**Generated:** 22-01-2026 11:32

---

## Executive Summary

- **Total Test Cases:** 21
- **Passed:** 0 (0.0%)
- **Failed:** 21 (100.0%)
- **Errors/No GT:** 0
- **Overall Pass Rate:** 0.0%

### Results by Difficulty

- **EASY:** 0/7 passed (0.0%)
- **MEDIUM:** 0/9 passed (0.0%)
- **HARD:** 0/5 passed (0.0%)


## Detailed Test Results

| # | Test Case | Difficulty | Status | Accuracy | Fields | Notes |
|---|-----------|------------|--------|----------|--------|-------|
| 1 | batch1-0001.jpg | EASY | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 2 | batch1-0002.jpg | EASY | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 3 | batch1-0003.jpg | EASY | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 4 | batch1-0004.jpg | MEDIUM | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 5 | batch1-0005.jpg | MEDIUM | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 6 | batch1-0006.jpg | MEDIUM | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 7 | batch1-0007.jpg | HARD | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 8 | batch1-0008.jpg | MEDIUM | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 9 | batch1-0009.jpg | EASY | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 10 | batch1-0010.jpg | EASY | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 11 | batch1-0011.jpg | EASY | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 12 | batch1-0012.jpg | MEDIUM | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 13 | batch1-0013.jpg | MEDIUM | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 14 | batch1-0014.jpg | EASY | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 15 | batch1-0015.jpg | HARD | ✗ FAILED | 0.0% | 0/0 | SUCCESS |
| 16 | pdf-1.pdf | HARD | ✗ FAILED | 0.0% | N/A | <HttpError 400 when requesting |
| 17 | pdf-2.pdf | MEDIUM | ✗ FAILED | 0.0% | N/A | 429 You exceeded your current  |
| 18 | pdf-3.pdf | MEDIUM | ✗ FAILED | 0.0% | N/A | 429 You exceeded your current  |
| 19 | pdf-4.pdf | HARD | ✗ FAILED | 0.0% | N/A | 429 You exceeded your current  |
| 20 | pdf-5.pdf | HARD | ✗ FAILED | 0.0% | N/A | 429 You exceeded your current  |
| 21 | pdf-6.pdf | MEDIUM | ✗ FAILED | 0.0% | N/A | 429 You exceeded your current  |


## Test Gates Analysis

### Gate 1: Basic OCR Extraction
- **Pass Rate:** 0/15 (0.0%)
- **Status:** FAILED

### Gate 2: PDF Processing
- **Pass Rate:** 0/6 (0.0%)
- **Status:** NEEDS REVIEW

### Gate 3: Multi-Invoice Detection
- **Test Case:** pdf-1.pdf (2 invoices)
- **Status:** PENDING
- **Note:** Requires API access for validation
