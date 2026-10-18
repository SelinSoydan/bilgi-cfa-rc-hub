"""Fixed content: rubric, roles, the CFA-way map and the Borusan document library."""

COLORS = ["#b0182d", "#2f5f95", "#2b7655", "#a2660b", "#6b4fa0", "#0f7c8c", "#c0543a", "#4a5568"]
COLS = [("todo", "To do", "#9aa0aa"), ("doing", "Doing", "#e6a640"), ("done", "Done", "#2b7655")]
WIP = 2
ROAD = ("2026-10-19", "2027-02-28")

SECTIONS = {
    "BD": ("Business description", 5, "#8a8f98", "What does Borusan sell, to whom, and where?"),
    "IND": ("Industry & competition", 10, "#2f5f95", "Is this a good industry, and is Borusan stronger than its peers?"),
    "INV": ("Investment summary", 15, "#6b4fa0", "In one page, why should an investor care? We write it last."),
    "VAL": ("Valuation", 20, "#b0182d", "How did we turn forecasts into a value, and why do we trust it?"),
    "FIN": ("Financial analysis", 20, "#a2660b", "What do the numbers say about the past, and do they support our forecast?"),
    "RISK": ("Investment risks", 15, "#0f7c8c", "What could make us wrong, and how much would it cost?"),
    "ESG": ("ESG", 15, "#2b7655", "Which environmental, social and governance issues truly change value?"),
}
REPORT_ORDER = ["BD", "IND", "INV", "VAL", "FIN", "RISK", "ESG"]
QUESTION_ORDER = ["BD", "IND", "FIN", "VAL", "RISK", "ESG", "INV"]
PRES = [("Financial analysis", 20, "#a2660b"), ("Valuation", 20, "#b0182d"), ("Presentation", 20, "#6b4fa0"),
        ("Q&A", 20, "#2f5f95"), ("ESG", 10, "#2b7655"), ("Team", 5, "#0f7c8c"), ("Slides", 5, "#8a8f98")]

ROLES = {
    "val": ("Valuation", ["VAL", "INV"], "Builds the DCF and the multiples check. Writes the first draft of the target price and the sensitivity table.", ["guidance", "pres2q26", "rating", "damodaran"]),
    "fin": ("Financial analysis", ["FIN"], "Five years of numbers in US dollars, the key ratios, and the link from past to forecast.", ["fr2q26", "fr2025", "fr2024", "fr2023", "earn2q26"]),
    "ind": ("Industry & business", ["IND", "BD"], "What Borusan sells and to whom, the demand chain, peers, tariffs.", ["ar2025", "pres2q26", "usorder", "tenaris"]),
    "esg": ("ESG & risks", ["ESG", "RISK"], "The ESG issues that change value, and the risk matrix with price impact.", ["tsrs2025", "sr2024", "rating", "cgov"]),
    "ed": ("Editor & slides", [], "One voice across the report, Harvard citations, charts and slides.", ["ar2025", "pres2q26"]),
}

PHASES = {"1.1": "1.1 Sector", "1.2": "1.2 Borusan & news", "1.3": "1.3 Financials", "1.4": "1.4 Earnings quality",
          "2": "2 Forecast", "3": "3 Model", "4": "4 Value", "5": "5 Conclusion"}

NKIND = {"note": ("Insight", "#2f5f95"), "meeting": ("Meeting", "#2b7655"), "question": ("Kickoff question", "#b0182d"),
         "ai": ("AI use", "#a2660b"), "help": ("Help hour", "#676b74")}

ZONES = [("Step 1", "2026-10-19", "2026-11-08", "#8a8f98"), ("Step 2", "2026-11-09", "2026-11-22", "#a2660b"),
         ("Step 3", "2026-11-23", "2026-11-30", "#6b4fa0"), ("Step 4", "2026-12-01", "2026-12-31", "#b0182d"),
         ("Step 5", "2027-01-01", "2027-01-31", "#2f5f95"), ("Final prep", "2027-02-01", "2027-02-28", "#2b7655")]

MAP = [
    {"n": 1, "t": "Understand the business", "when": "Oct 19 to Nov 8", "secs": "Business 5 · Industry 10",
     "cfa": "Before any number, learn how the company makes money, who it competes with, and whether its industry is a good place to be.",
     "ours": "First we learn how the steel pipe business works. Then we read Borusan's own documents to see what it sells and where its money comes from. Its profit margin swings a lot: 18.2% in 2023, but only 6.0% in 2024.",
     "out": "Each of us can tell Borusan's story in three sentences.",
     "parts": [
         {"id": "1.1", "t": "Sector", "s": "2026-10-19", "e": "2026-10-22", "cfa": "Is steel a good industry to be in? Is Borusan stronger than its competitors?", "ours": "We learn how a pipe maker earns money: it buys steel coil, turns it into pipe, and keeps the difference. We look at what past crises did to steel companies, and compare Borusan's margins with the sector."},
         {"id": "1.2", "t": "Borusan & news", "s": "2026-10-23", "e": "2026-10-25", "cfa": "Use the right sources: the company's own reports, official filings on KAP, and industry data.", "ours": "We read Borusan's investor presentation and annual report. We find out what it sells, who buys it, and how much of the money comes from the US. We also check the latest news."},
         {"id": "1.3", "t": "Financials", "s": "2026-10-26", "e": "2026-10-29", "cfa": "Do the numbers tell the same story as the company?", "ours": "We put five years of results in US dollars side by side. We find out why the margin fell from 2023 to 2024, how much debt Borusan has, and how it compares with the sector."},
         {"id": "1.4", "t": "Earnings quality", "s": "2026-10-30", "e": "2026-11-01", "cfa": "Is the profit real, or did one-time events make it look bigger?", "ours": "We look for one-time items, like selling a building. We check that the cash coming in matches the profit. Then we write a clean profit number for each year."},
     ]},
    {"n": 2, "t": "Forecast the future", "when": "Nov 9 to Nov 22, after the kickoff and the Q3 results", "secs": "Financial analysis 20",
     "cfa": "Predict the future from the things that drive the business, not by copying the past.",
     "ours": "We forecast sales as tons sold times price per ton, for each part of the business. We use the margin of a normal year, not the best or the worst one. The company's own forecast is something we check against, not something we copy.",
     "out": "A forecast table where every number has a reason and a source."},
    {"n": 3, "t": "Choose the method", "when": "Nov 23 to Nov 30", "secs": "Valuation 20",
     "cfa": "Pick the valuation method that fits this company. Often two methods that check each other.",
     "ours": "Our main method is a DCF: we add up the cash Borusan will make in the future, in US dollars, and bring it back to today's value. Then we check it against how the market prices similar companies, like Tenaris.",
     "out": "One page that explains why this method fits Borusan."},
    {"n": 4, "t": "Turn the forecast into a value", "when": "December", "secs": "Valuation 20",
     "cfa": "Use the method carefully: the right cash, with the right discount rate.",
     "ours": "We build the discount rate from the risk of the steel sector and of the countries where Borusan has factories. We find the value of the whole company, subtract its debt, and divide by the number of shares.",
     "out": "A target price per share, and a range we can defend."},
    {"n": 5, "t": "Make the call", "when": "January, then the final in February", "secs": "Summary 15 · Risks 15 · ESG 15",
     "cfa": "Compare our value with today's share price and decide what an investor should do.",
     "ours": "Page 1 of the report says Buy, Hold or Sell, with three reasons. We show the biggest risks and how much each one could change the price. We include only the ESG topics that really change the value, like carbon costs (CBAM).",
     "out": "The 10-page report, then the slides for the final."},
]

BP = "https://borusanpipe.com/"
DOCS = [
    ("Read first", "pres2q26", "2Q 2026 Investor Presentation", "7 Aug 2026", BP + "Uploads/investor/docs/2026/yatirimci-sunumlari/Borusan-Pipe-Investor-Presentation-2Q26.pdf", "Management tells its own story in slides. It is the fastest way to start.", "Look at how sales are split between the four business areas, and how sales volume and EBITDA changed each quarter.", ["INV", "FIN"]),
    ("Read first", "ar2025", "2025 Annual Report", "12 Mar 2026", BP + "Uploads/investor/docs/faaliyetRaporlari/Borusan-Boru-2025-Yili-Faaliyet-Raporu-en.pdf", "The full story of the year: strategy, factories, countries, risks and who runs the company.", "Look at the business areas, where the factories and customers are, and the section on risks.", ["BD", "IND", "RISK"]),
    ("Read first", "guidance", "Guidance page", "updated each quarter", BP + "investor-relations/guidance", "The company's own forecast for this year, next to its results since 2021.", "Look at the EBITDA margin row. It shows the steel cycle in one line.", ["VAL", "FIN"]),
    ("The numbers", "fr2q26", "2Q 2026 Financial Report", "7 Aug 2026", BP + "Uploads/investor/docs/2026/finansal-raporlar/borusan-boru-finansal-rapor-2c26.pdf", "The latest official financial statements, with notes that explain them.", "Look at the note on debt, the note on business segments, and the cash flow statement.", ["FIN", "VAL"]),
    ("The numbers", "fr2025", "2025 Financial Report", "26 Feb 2026", BP + "Uploads/investor/docs/financial-reports/2025-financial-statement.pdf", "The checked (audited) financial statements for the whole of 2025.", "Look at the income statement, the balance sheet and the cash flow statement.", ["FIN"]),
    ("The numbers", "fr2024", "2024 Financial Report", "21 Feb 2025", BP + "Uploads/investor/docs/financial-reports/brsan_122024.pdf", "The audited statements for 2024, the year the margin was low.", "Find out why the margin fell: lower prices, higher costs, or fewer tons sold?", ["FIN"]),
    ("The numbers", "fr2023", "2023 Financial Report", "1 Mar 2024", BP + "Uploads/raporlar/finansal_raporlar/brsan_122023.pdf", "The audited statements for 2023, the year the margin was high.", "See what a strong year looks like, and read about buying Berg Pipe.", ["FIN"]),
    ("The numbers", "earn2q26", "2Q 2026 Earnings Announcement", "7 Aug 2026", BP + "Uploads/investor/docs/2026/duyurular/borusan-pipe-earnings-announcement-2q26.pdf", "A short summary of the quarter, in the company's own words.", "Look at the main numbers and at what management says caused them.", ["FIN", "INV"]),
    ("ESG", "tsrs2025", "TSRS Sustainability Report 2025", "2025", BP + "Content/assets/pdf/reports/Borusan-Birlesik-Boru-TSRS-Report.pdf", "A sustainability report under Türkiye's new rules (TSRS). It puts a money value on climate risks.", "Look at the climate risks and opportunities, the emissions, and the plan to cut them.", ["ESG", "RISK"]),
    ("ESG", "sr2024", "Sustainability Report 2024", "2024", BP + "Content/assets/pdf/reports/Borusan-Pipe-Sustainability-Report-2024.pdf", "Emissions, energy, safety and people, year by year.", "Look at how emissions changed, how much power is renewable, and the safety record.", ["ESG"]),
    ("Risk and governance", "rating", "Credit rating announcement", "28 Aug 2026", BP + "Uploads/investor/docs/2026/ozel-durum-aciklamalari/credit-rating-28092026.pdf", "How a rating agency judges Borusan's ability to pay back its debt.", "Look at the rating and the outlook. It helps us estimate what Borusan pays to borrow.", ["VAL", "RISK"]),
    ("Risk and governance", "cgov", "Shareholder structure", "current", BP + "investor-relations/corporate-governance/partnership-structure", "Who owns the company, and how many shares trade freely on the stock market.", "Look at the main owners and the free float (shares anyone can buy).", ["BD", "ESG"]),
    ("News", "usorder", "New sales order in the US", "21 Aug 2026", BP + "Uploads/investor/docs/2026/ozel-durum-aciklamalari/receipt-of-new-sales-order-in-the-united-states-of-america.pdf", "An official announcement of a new order from a US customer.", "Look at how big the order is and when it will be delivered. It tells us about future sales.", ["IND", "FIN"]),
    ("News", "news", "All official announcements", "live", BP + "investor-relations/announcements/material-disclosures", "Every official announcement, newest first.", "Look for new orders, rating changes and the dates of the next results.", ["IND"]),
    ("Outside sources", "damodaran", "Damodaran data: betas, risk premiums, margins", "updated each January", "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html", "Free data from an NYU professor. We use it for the discount rate and to compare with the sector.", "Look for the Steel row in the margins and betas tables, and Türkiye's country risk premium.", ["VAL"]),
    ("Outside sources", "tenaris", "Tenaris annual filing 2025 (Form 20-F)", "2026", "https://www.sec.gov/Archives/edgar/data/0001190723/000155485526000490/ts-20251231.htm", "The yearly report of a big global pipe maker, our closest competitor.", "Look at sales by region and how they explain the ups and downs of the pipe business.", ["IND"]),
]
DOC = {d[1]: d for d in DOCS}
