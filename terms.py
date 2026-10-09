"""Intellics financial terms: 609 unique terms, shown 10 a day with no repeats for 60 days.

Each line is: Term|Category|Meaning|Example
The list is shuffled with a fixed seed, so every day mixes topics but the order never changes.
"""
import random

_RAW = """Share|Markets|A small slice of ownership in a company.|Owning 10 shares makes you a tiny part-owner of that company.
Stock exchange|Markets|A marketplace where shares are bought and sold, such as the NSE or BSE.|Your broker sends your order and the exchange matches you with a seller.
Bull market|Markets|A long period when share prices keep rising and investors feel confident.|The Sensex climbing for many months is called a bull run.
Bear market|Markets|A period when prices fall 20% or more from a high and fear spreads.|Markets dropping 25% from their peak is a bear market.
Blue-chip stock|Markets|A share of a large, well-known and financially strong company.|TCS and HDFC Bank are often called blue chips.
Penny stock|Markets|A very cheap share of a tiny company, often risky and hard to sell.|A Rs 3 share with few buyers can be hard to exit.
Large-cap|Markets|One of the biggest listed companies, usually the top 100 by market value.|Reliance is a large-cap company.
Mid-cap|Markets|A medium-sized listed company, ranked roughly 101st to 250th by market value.|A fast-growing company outside the top 100 is often a mid-cap.
Small-cap|Markets|A smaller listed company ranked below the top 250, with higher growth and higher risk.|Small-caps can double quickly but also fall quickly.
Index|Markets|A basket of selected shares that shows how a market or sector is doing.|The Nifty 50 tracks 50 large companies on the NSE.
Benchmark|Markets|A standard, usually an index, used to judge how well an investment performed.|A fund that returns 12% when its benchmark returns 10% beat the market.
Free float|Markets|The shares actually available for the public to trade, leaving out promoter holdings.|If promoters hold 60%, the free float is about 40%.
Liquidity|Markets|How quickly something can be sold for cash without moving its price much.|A large-cap share is easy to sell; a tiny company's share may not be.
Volatility|Markets|How sharply and how often a price swings up and down.|A share that moves 5% every day is very volatile.
Bid price|Trading|The highest price a buyer is currently willing to pay for a share.|The best buyer offers Rs 100 for a share.
Ask price|Trading|The lowest price a seller is currently willing to accept for a share.|The best seller wants Rs 100.50.
Bid-ask spread|Trading|The gap between the bid and ask prices; a small gap means an easy-to-trade share.|Bid Rs 100 and ask Rs 100.50 gives a spread of 50 paise.
Market order|Trading|An order to buy or sell immediately at the best price available.|You press buy and get filled at the current market price.
Limit order|Trading|An order to buy or sell only at your chosen price or better.|You place a buy order at Rs 95 and wait for the price to fall.
Stop-loss order|Trading|An order that sells automatically if the price falls to a set level, to cap your loss.|You bought at Rs 100 and set a stop-loss at Rs 92.
Circuit breaker|Trading|A rule that pauses trading when the market moves too much too fast.|Trading halts for a while if the Nifty falls 10% in a day.
Demat account|Trading|An account that holds your shares in electronic form instead of paper certificates.|Your bought shares appear in your demat account.
Trading account|Trading|The account you use to place buy and sell orders on the exchange.|You use your broker's app to trade through this account.
T+1 settlement|Trading|Shares and money change hands one working day after the trade.|Buy on Monday and the shares reach your demat on Tuesday.
Dividend yield|Valuation|Yearly dividend as a percentage of the current share price.|Rs 5 dividend on a Rs 100 share is a 5% yield.
Dividend payout ratio|Valuation|The share of profit a company pays out to shareholders as dividends.|Paying Rs 40 out of Rs 100 profit is a 40% payout.
Ex-dividend date|Corporate|The cut-off date; you must own the share before it to get the upcoming dividend.|Buy after the ex-date and the dividend goes to the previous owner.
Record date|Corporate|The date the company checks its books to see who gets a dividend or other benefit.|Only holders on the record date receive the bonus shares.
Stock split|Corporate|A company divides each share into more shares, so the price per share drops.|A 1-for-2 split turns one Rs 1,000 share into two Rs 500 shares.
Bonus shares|Corporate|Free extra shares given to existing shareholders out of company reserves.|A 1:1 bonus doubles the number of shares you own.
Rights issue|Corporate|An offer to existing shareholders to buy new shares, usually at a discount.|You may buy 1 new share for every 5 you hold at a lower price.
Share buyback|Corporate|A company buys its own shares back from investors, reducing shares in the market.|A buyback at Rs 600 when the market price is Rs 500 rewards sellers.
Delisting|Corporate|Removing a company's shares from the stock exchange.|After delisting you can no longer trade that share on the exchange.
Listing|Corporate|The day a company's shares start trading on an exchange.|An IPO company lists a few days after the issue closes.
Anchor investor|IPO|A big institution that buys into an IPO a day before it opens to the public.|Mutual funds often act as anchor investors.
Grey market premium|IPO|An unofficial extra price people pay for IPO shares before listing.|A positive premium hints at a strong listing, but it is not guaranteed.
Oversubscription|IPO|When investors apply for more shares than the company is offering.|An IPO subscribed 30 times means 30 applications for every share on offer.
Lot size|IPO|The minimum bundle of shares or contracts you must buy at one time.|An IPO may need a minimum bid of 100 shares.
Face value|Corporate|The original nominal value of a share, which has little to do with its market price.|A Rs 2 face value share can trade at Rs 1,500.
Book value|Valuation|What a company is worth on paper: its assets minus its liabilities.|Assets of Rs 500 crore and debts of Rs 200 crore give Rs 300 crore.
Promoter|Corporate|The founders or main owners who control a company.|The Tata family and Reliance's Ambani family are promoters of their companies.
Promoter holding|Corporate|The percentage of a company that its promoters own.|A falling promoter holding can worry investors.
Pledged shares|Corporate|Shares that promoters have put up as security for a loan.|If the price crashes, lenders may sell the pledged shares.
Insider trading|Regulation|Illegal trading based on important secret information that is not yet public.|Buying before a merger announcement using confidential news is insider trading.
Bulk deal|Trading|A trade of more than 0.5% of a company's shares in a single day.|Exchanges publish bulk deals so everyone can see them.
Short selling|Trading|Selling borrowed shares hoping to buy them back cheaper later.|You sell at Rs 100, the price falls to Rs 80, you buy back and keep Rs 20.
Margin trading|Trading|Trading with money borrowed from your broker to take a larger position.|You put in Rs 1 lakh and trade Rs 3 lakh worth of shares.
Margin call|Trading|A broker's demand to add money when your losses shrink your margin.|You must top up your account or the broker may sell your positions.
Leverage|Trading|Using borrowed money to increase the size of a bet, which magnifies gains and losses.|5x leverage turns a 2% fall into a 10% loss.
Square off|Trading|Closing a trade by doing the opposite action, for example selling what you bought.|Day traders square off positions before the market closes.
Delivery trading|Trading|Buying shares and holding them beyond the day so they reach your demat account.|You buy 10 shares and keep them for a year.
Swing trading|Trading|Holding shares for days or weeks to profit from short-term price swings.|You buy on a dip and sell after a 5% bounce a week later.
Positional trading|Trading|Holding a trade for weeks or months based on a larger trend.|You ride an uptrend in a bank share for three months.
Scalping|Trading|Making many quick trades for tiny profits within seconds or minutes.|A scalper aims for a few paise per share, many times a day.
Value investing|Strategy|Buying shares that look cheap compared with what the business is truly worth.|You buy a profitable company trading below its book value.
Growth investing|Strategy|Buying companies expected to grow sales and profits faster than the others.|You pick a fast-growing company even at a high price.
Momentum investing|Strategy|Buying what has been rising, betting that the trend continues.|You buy shares at 52-week highs.
Dividend investing|Strategy|Choosing shares mainly for the regular dividend income they pay.|You hold companies with long records of paying dividends.
Contrarian investing|Strategy|Going against the crowd by buying when others are fearful.|You buy a good company after bad news has crushed its price.
Buy and hold|Strategy|Buying quality investments and keeping them for many years.|You hold a good company through ups and downs for 10 years.
Rupee cost averaging|Strategy|Investing a fixed amount regularly so you buy more units when prices are low.|A Rs 5,000 monthly SIP buys more units in a falling market.
Portfolio|Strategy|The complete collection of your investments.|Your shares, mutual funds and gold together form your portfolio.
Asset allocation|Strategy|Deciding how to split your money among shares, bonds, gold and cash.|You keep 60% in equity, 30% in debt and 10% in gold.
Rebalancing|Strategy|Adjusting your portfolio back to your planned mix of investments.|If equity grows to 70%, you sell some to return to 60%.
Sector rotation|Strategy|Moving money from one industry to another as the economy changes.|Investors shift from banks to IT when growth slows.
Cyclical stock|Markets|A share whose fortunes rise and fall with the economy, such as cars or steel.|Car makers sell more in good times and less in bad times.
Defensive stock|Markets|A share of a business people need in any economy, such as food or medicine.|FMCG companies often fall less when markets crash.
Growth stock|Markets|A share of a company expected to grow faster than the overall market.|A young tech company reinvesting all its profit.
Value stock|Markets|A share trading at a low price compared with its earnings or assets.|A steady company with a P/E far below its peers.
Turnaround stock|Markets|A share of a struggling company that is trying to recover.|A company cutting debt and returning to profit.
Multibagger|Markets|A share whose price rises many times over your buying price.|A Rs 50 share rising to Rs 500 is a ten-bagger.
Bellwether|Markets|A company whose performance signals how its industry or market is heading.|Strong TCS results often lift the whole IT sector.
Market breadth|Technical|How many shares are rising compared with falling; shows how wide a rally is.|Index up but most shares down means a narrow rally.
Advance-decline ratio|Technical|The number of rising shares divided by the number of falling shares.|1,500 gainers and 500 losers gives a ratio of 3.
Gap up|Technical|When a share opens higher than the previous close with no trading in between.|Closes at Rs 100, opens at Rs 106 after good news.
Gap down|Technical|When a share opens lower than the previous close with no trading in between.|Closes at Rs 100, opens at Rs 92 after bad results.
Rally|Markets|A sharp and sustained rise in prices.|Banks rallied 8% in a week after the rate cut.
Correction|Markets|A fall of 10% or more from a recent high.|The market slipping 12% from its peak is a correction.
Market crash|Markets|A sudden and steep drop in prices, often driven by panic.|Prices fall 10% in a day as everyone rushes to sell.
Bubble|Markets|Prices rising far above real value because of hype, until they burst.|Everyone buys a trendy sector at any price, then it collapses.
Dead cat bounce|Markets|A small, short recovery during a long fall that soon fades.|A share rises 3% for two days and then keeps falling.
Short squeeze|Trading|A rush of forced buying by short sellers that pushes a price sharply higher.|Short sellers rush to buy back and drive the price even higher.
Pump and dump|Regulation|A scam where a share is hyped up and then sold to unsuspecting buyers.|Social media tips push a tiny share up before the seller exits.
Price band|Trading|The daily limit within which a share price is allowed to move.|A share in a 5% band cannot rise or fall more than 5% in a day.
Pre-open session|Trading|A short window before the market opens used to set the opening prices.|Orders collected between 9:00 and 9:08 decide the opening price.
Closing price|Trading|The final price of a share at the end of the trading day.|The price used to calculate the day's gain or loss.
Opening price|Trading|The first price at which a share trades when the market opens.|It can differ from yesterday's close after overnight news.
Ticker symbol|Trading|A short code that identifies a listed company.|INFY stands for Infosys.
52-week range|Technical|The lowest and highest prices a share touched in the last year.|A range of Rs 80 to Rs 120 shows how much the price has swung.
Support level|Technical|A price where a falling share often finds buyers and stops dropping.|The price bounced from Rs 200 three times, so Rs 200 is support.
Resistance level|Technical|A price where a rising share often meets sellers and stops climbing.|The price keeps failing at Rs 300, so Rs 300 is resistance.
Candlestick chart|Technical|A chart showing open, high, low and close for each period as a candle shape.|A green candle means the price closed higher than it opened.
Retail investor|Markets|An ordinary individual investing their own money rather than an institution.|A student investing Rs 500 a month is a retail investor.
Institutional investor|Markets|A big organisation, such as a mutual fund or insurer, that invests huge sums.|LIC buying a large stake in a company.
DII|Markets|Domestic institutional investors: Indian mutual funds, insurers and banks that invest in the market.|DIIs often buy when foreign investors sell.
P/E ratio|Valuation|Price divided by earnings per share: how much investors pay for each rupee of yearly profit.|A P/E of 20 means investors pay Rs 20 for every Rs 1 of profit.
P/B ratio|Valuation|Share price divided by book value per share.|A P/B of 2 means the market values the company at twice its book value.
PEG ratio|Valuation|The P/E ratio divided by the expected profit growth rate; adjusts P/E for growth.|P/E 30 with 30% growth gives a PEG of 1.
EV/EBITDA|Valuation|Enterprise value divided by EBITDA; compares companies regardless of their debt.|A lower multiple can mean a cheaper company.
Enterprise value|Valuation|Market cap plus debt minus cash: the price of buying the whole business.|A company worth Rs 1,000 crore with Rs 200 crore debt and Rs 100 crore cash has EV Rs 1,100 crore.
EPS|Valuation|Earnings per share: the company's profit divided by its number of shares.|Rs 100 crore profit and 10 crore shares gives Rs 10 EPS.
Book value per share|Valuation|The company's net worth divided by the number of shares.|Net worth Rs 500 crore with 5 crore shares gives Rs 100 per share.
Return on equity|Ratios|Profit earned on the shareholders' money, shown as a percentage.|Rs 15 profit on Rs 100 of equity is a 15% ROE.
Return on assets|Ratios|How much profit a company makes from each rupee of its assets.|Rs 5 profit from Rs 100 of assets is a 5% ROA.
ROCE|Ratios|Return on capital employed: profit before interest and tax divided by capital used in the business.|A higher ROCE means the business uses money well.
Debt-to-equity ratio|Ratios|How much the company has borrowed for every rupee of its own money.|Debt of Rs 50 against equity of Rs 100 gives 0.5.
Interest coverage ratio|Ratios|How many times a company's operating profit can pay its interest bill.|A ratio of 5 means profit is five times the interest due.
Current ratio|Ratios|Current assets divided by current liabilities; shows ability to pay short-term bills.|A ratio above 1 means short-term assets cover short-term dues.
Quick ratio|Ratios|Like the current ratio but leaves out inventory, which is slower to turn into cash.|A strict test of short-term strength.
Gross margin|Ratios|Revenue minus the direct cost of making the product, as a percentage of revenue.|Selling at Rs 100 with Rs 60 production cost gives a 40% gross margin.
Operating margin|Ratios|Operating profit as a percentage of revenue, before interest and tax.|Rs 18 operating profit on Rs 100 sales is an 18% margin.
Net profit margin|Ratios|The percentage of revenue left as profit after all costs.|Earning Rs 10 profit on Rs 100 of sales is a 10% margin.
Free cash flow|Cash flow|Cash left after running the business and paying for investments in equipment.|A company with strong free cash flow can pay dividends and reduce debt.
Operating cash flow|Cash flow|Cash a company generates from its day-to-day business.|Profit can look good while cash flow is weak.
Cash flow statement|Accounting|A report showing cash coming in and going out over a period.|It shows whether profit is turning into real cash.
Balance sheet|Accounting|A snapshot of what a company owns, owes and is worth on a given date.|Assets equal liabilities plus equity.
Profit and loss statement|Accounting|A report showing revenue, costs and profit over a period.|Also called the income statement.
Revenue|Accounting|The money a company earns from selling its goods or services.|A shop selling Rs 10 lakh of goods has Rs 10 lakh revenue.
Turnover|Accounting|Another word for total sales or revenue in a period.|Annual turnover of Rs 50 crore.
Net profit|Accounting|What is left after subtracting all expenses and taxes from revenue.|Also called the bottom line.
Operating profit|Accounting|Profit from the main business before interest and taxes.|Rs 30 crore operating profit before paying interest.
PAT|Accounting|Profit after tax: the final profit available to shareholders.|Results headlines often quote PAT.
PBT|Accounting|Profit before tax: profit after all costs but before paying tax.|PBT of Rs 100 crore and tax of Rs 25 crore leaves PAT of Rs 75 crore.
EBIT|Accounting|Earnings before interest and tax: profit from operations.|Used to compare companies with different debt levels.
Depreciation|Accounting|Spreading the cost of a machine or building over the years it is used.|A Rs 10 lakh machine losing Rs 1 lakh of value each year.
Amortisation|Accounting|Spreading the cost of an intangible asset, such as a licence, over its life.|A Rs 5 crore licence written off over five years.
Goodwill|Accounting|The extra price paid for a business above the value of its assets.|Paying Rs 120 crore for a company with Rs 100 crore of assets creates Rs 20 crore goodwill.
Intangible assets|Accounting|Valuable things you cannot touch, such as brands, patents and software.|A famous brand name is an intangible asset.
Working capital|Accounting|Current assets minus current liabilities: money available for daily operations.|Rs 50 crore of short-term assets minus Rs 30 crore dues leaves Rs 20 crore.
Inventory turnover|Ratios|How many times a company sells and replaces its stock in a year.|A turnover of 12 means stock is sold roughly every month.
Receivable days|Ratios|The average number of days customers take to pay their bills.|45 days means customers pay in about a month and a half.
Payable days|Ratios|The average number of days a company takes to pay its suppliers.|Longer payable days can ease cash needs but strain suppliers.
Cash conversion cycle|Ratios|The days between paying for stock and getting cash from customers.|A shorter cycle means cash comes back faster.
Asset turnover|Ratios|Revenue divided by assets: how well assets are used to create sales.|Rs 200 crore of sales on Rs 100 crore of assets is a turnover of 2.
DuPont analysis|Ratios|Breaking ROE into margin, asset use and leverage to see what drives it.|Two companies with the same ROE can get it in very different ways.
Capital expenditure|Corporate|Money spent on buying or upgrading long-lasting assets such as factories.|Building a new plant is capex.
Retained earnings|Accounting|Profit a company keeps for itself instead of paying out as dividends.|Rs 100 crore profit with Rs 30 crore dividend retains Rs 70 crore.
Reserves and surplus|Accounting|Profits and other amounts the company has saved over the years.|It forms a big part of shareholders' funds.
Share capital|Accounting|The money the company raised by issuing shares.|It appears on the balance sheet under equity.
Equity|Accounting|The owners' stake: assets minus liabilities.|A home worth Rs 80 lakh with a Rs 50 lakh loan has Rs 30 lakh equity.
Liability|Accounting|Something a company owes to others, such as loans or unpaid bills.|A bank loan is a liability.
Asset|Accounting|Anything a company owns that has value.|Cash, machines and buildings are assets.
Current liabilities|Accounting|Debts and bills due within a year.|Supplier dues payable next month.
Fixed assets|Accounting|Long-term assets used to run the business, such as land and machines.|A factory building.
Contingent liability|Accounting|A possible future debt that depends on an uncertain event, like a court case.|A tax dispute that may cost Rs 50 crore if lost.
Accrual accounting|Accounting|Recording income and costs when they are earned or incurred, not when cash moves.|A sale made on credit is counted as revenue straight away.
Statutory audit|Accounting|A yearly independent check of a company's accounts as required by law.|Auditors give an opinion on whether accounts are fair.
Qualified audit opinion|Accounting|An auditor's warning that some part of the accounts is not fully reliable.|A red flag investors should read carefully.
Related-party transaction|Corporate|A deal between a company and people or firms connected to it.|Buying goods from a promoter's other company.
Consolidated results|Accounting|Combined accounts of a parent company and all its subsidiaries.|It shows the whole group, not just one entity.
Standalone results|Accounting|Accounts of a single company, without its subsidiaries.|Used to see the parent's own performance.
Year-on-year growth|Analysis|Comparing a number with the same period one year ago.|Q2 profit up 12% versus Q2 last year.
Quarter-on-quarter growth|Analysis|Comparing a number with the immediately preceding quarter.|Q2 sales up 3% over Q1.
Management guidance|Analysis|The company's own forecast of its future sales or profit.|Management guides for 15% revenue growth.
Earnings call|Analysis|A call where management explains results and answers analysts' questions.|Held soon after quarterly results.
Earnings surprise|Analysis|When actual profit differs from what analysts expected.|A profit beating estimates by 10% can lift the share price.
Annual report|Analysis|A yearly document with accounts, strategy and management's discussion.|A good place to read the full story of a company.
DRHP|IPO|Draft red herring prospectus: the draft IPO document filed with SEBI.|It lists the company's risks and finances before the IPO.
Cost of capital|Valuation|The return a company must earn to satisfy those who funded it.|If funds cost 10%, projects must earn more than 10%.
WACC|Valuation|Weighted average cost of capital: the blended cost of a firm's debt and equity.|Used as the discount rate in valuation.
CAPM|Valuation|A model that links the return investors expect to the risk-free rate and the share's risk.|Higher beta means a higher expected return.
Discounted cash flow|Valuation|Valuing a business by adding up its future cash flows in today's money.|Rs 110 next year is worth about Rs 100 today at 10%.
Terminal value|Valuation|The value of a business beyond the years you forecast in detail.|Often a large part of a DCF value.
Net present value|Valuation|Today's value of future cash flows minus the cost of an investment.|A positive NPV means the project adds value.
Internal rate of return|Valuation|The yearly return a project earns on the money put in.|An IRR of 14% beats a 10% cost of capital.
Payback period|Valuation|How long a project takes to earn back the money invested.|Rs 10 lakh recovered at Rs 2.5 lakh a year takes 4 years.
Time value of money|Valuation|The idea that money today is worth more than the same money later.|Rs 100 today can earn interest, so it beats Rs 100 next year.
Intrinsic value|Valuation|What an investment is truly worth based on its fundamentals, not its market price.|A share priced at Rs 80 with intrinsic value Rs 120 looks cheap.
Margin of safety|Valuation|Buying well below true value to leave room for mistakes.|Buying a Rs 100 value at Rs 70.
Economic moat|Strategy|A lasting advantage that protects a company from competitors.|A powerful brand or low costs.
Economies of scale|Strategy|Costs per unit fall as a company produces more.|A big factory makes each item cheaper.
Operating leverage|Strategy|How strongly profit rises when sales rise, because many costs are fixed.|High fixed costs mean a small sales rise gives a big profit jump.
Financial leverage|Strategy|Using debt to boost returns on equity.|Borrowing at 8% to earn 12%.
Capital structure|Corporate|The mix of debt and equity a company uses to fund itself.|60% equity and 40% debt.
Equity dilution|Corporate|Existing owners' share falls when new shares are issued.|Issuing new shares cuts your 10% stake to 8%.
ESOP|Corporate|Employee stock option plan: a right for staff to buy company shares cheaply.|Employees get options to buy shares at a fixed price.
Preference share|Corporate|A share paying a fixed dividend, with priority over ordinary shares if the company winds up.|Preference holders are paid before equity holders.
Debenture|Corporate|A loan certificate a company issues to borrow money from the public.|You lend Rs 1,000 and get fixed interest.
Holding company|Corporate|A company that owns controlling stakes in other companies.|It controls subsidiaries through ownership.
Subsidiary|Corporate|A company controlled by another company that owns most of its shares.|A parent firm owning 70% of a smaller firm.
Joint venture|Corporate|Two or more firms teaming up to run a project together.|Two companies share costs and profits of a new plant.
Hostile takeover|Corporate|An attempt to buy a company against the wishes of its management.|A bidder goes directly to shareholders with an offer.
Leveraged buyout|Corporate|Buying a company mainly with borrowed money, repaid from its own cash flows.|A fund buys a firm using 70% debt.
Demerger|Corporate|Splitting a company into separate listed companies.|A conglomerate spins off its power business.
Due diligence|Corporate|A detailed check of a company's facts before buying or investing.|Reviewing accounts, contracts and legal cases.
Comparable company analysis|Valuation|Valuing a company by comparing it with similar listed firms.|Using the average P/E of its peers.
Sum-of-the-parts valuation|Valuation|Valuing each business of a group separately and adding them up.|Valuing a conglomerate's retail and telecom arms one by one.
Book building|IPO|The process of discovering an IPO price from bids within a price range.|Investors bid between Rs 300 and Rs 320.
Greenshoe option|IPO|An option letting underwriters sell extra IPO shares to stabilise the price after listing.|It helps support the price in the early days.
Derivative|Derivatives|A contract whose value depends on the price of something else, such as a share or index.|A Nifty future gains or loses as the Nifty moves.
Futures contract|Derivatives|An agreement to buy or sell something at a fixed price on a fixed future date.|You agree today to buy a share at Rs 100 next month.
Options contract|Derivatives|A contract giving the right, but not the duty, to buy or sell at a fixed price.|You pay a small fee for the right to buy at Rs 100 later.
Call option|Derivatives|The right to buy at a fixed price before a set date.|You buy a call hoping the price goes up.
Put option|Derivatives|The right to sell at a fixed price before a set date.|You buy a put hoping the price goes down.
Strike price|Derivatives|The fixed price at which an option lets you buy or sell.|A call with a Rs 100 strike lets you buy at Rs 100.
Option premium|Derivatives|The price you pay to buy an option.|You pay Rs 5 per share to get the option.
Expiry date|Derivatives|The date on which a derivative contract ends.|Index options in India expire on set weekdays.
In the money|Derivatives|An option that already has value if exercised now.|A Rs 100 call when the share trades at Rs 110.
Out of the money|Derivatives|An option with no value if exercised now.|A Rs 100 call when the share trades at Rs 90.
At the money|Derivatives|An option whose strike price is about equal to the current price.|A Rs 100 call when the share is at Rs 100.
Time value|Derivatives|The part of an option's price that comes from time left until expiry.|It shrinks to zero as expiry nears.
Open interest|Derivatives|The total number of derivative contracts still open and not yet closed.|Rising open interest means new money entering.
Put-call ratio|Derivatives|Puts traded divided by calls traded; a gauge of market mood.|A very high ratio suggests nervousness.
Implied volatility|Derivatives|The market's guess of how much a price will move, built into option prices.|Option prices jump before big events as implied volatility rises.
India VIX|Derivatives|An index showing how much volatility the market expects in the next 30 days.|A rising VIX means traders expect bigger swings.
Option Greeks|Derivatives|Measures that show how an option's price responds to changes such as price and time.|Delta, gamma, theta and vega are Greeks.
Delta|Derivatives|How much an option's price changes when the underlying price moves by Re 1.|A delta of 0.5 means Rs 0.50 change for Rs 1 move.
Gamma|Derivatives|How fast delta itself changes as the price moves.|High gamma makes an option react sharply.
Theta|Derivatives|How much value an option loses each day as expiry gets closer.|Theta is the daily cost of holding an option.
Vega|Derivatives|How much an option's price changes when expected volatility changes.|Vega rises when uncertainty rises.
Hedging|Derivatives|Taking a second position to reduce the risk of the first.|Buying a put to protect shares you own.
Arbitrage|Derivatives|Profiting from a price difference of the same thing in two places.|Buying in one market at Rs 100 and selling in another at Rs 101.
Speculation|Derivatives|Taking a risky bet hoping to profit from price moves.|Buying options purely hoping for a quick jump.
Straddle|Derivatives|Buying a call and a put at the same strike to profit from a big move either way.|Used before big announcements.
Strangle|Derivatives|Buying a call and a put at different strikes to profit from a big move either way.|Cheaper than a straddle but needs a bigger move.
Covered call|Derivatives|Selling a call against shares you own to earn extra income.|You hold shares and sell a call above today's price.
Protective put|Derivatives|Buying a put on shares you own to limit losses.|It works like insurance on your shares.
Bull call spread|Derivatives|Buying one call and selling a higher call to cap both cost and profit.|A lower-cost way to bet on a rise.
Bear put spread|Derivatives|Buying one put and selling a lower put to cap both cost and profit.|A lower-cost way to bet on a fall.
Iron condor|Derivatives|A four-leg options strategy that earns when the price stays in a range.|Profits if the Nifty stays calm until expiry.
Rollover|Derivatives|Closing a near-expiry futures position and opening the same one in the next month.|You roll your position to carry it forward.
SPAN margin|Derivatives|The main margin required to cover possible losses on a derivatives position.|Calculated by the exchange based on risk.
Exposure margin|Derivatives|Extra margin collected on top of SPAN margin to cover unexpected moves.|Taken as a percentage of the contract value.
Cash settlement|Derivatives|Settling a contract in cash instead of delivering the actual asset.|Index options settle in cash.
Physical settlement|Derivatives|Settling a contract by actually delivering the shares.|Stock derivatives in India settle by delivery.
Index futures|Derivatives|Futures contracts based on an index such as the Nifty.|Used to bet on or hedge the whole market.
Weekly expiry|Derivatives|Options contracts that end each week instead of each month.|Popular with short-term traders.
RSI|Technical|Relative strength index: a 0 to 100 gauge of whether a price has risen or fallen too fast.|Above 70 is often called overbought, below 30 oversold.
MACD|Technical|An indicator comparing two moving averages to show the strength and direction of a trend.|A crossover of its lines is used as a signal.
Bollinger Bands|Technical|Bands drawn around a moving average that widen and narrow with volatility.|A price touching the upper band may be stretched.
Fibonacci retracement|Technical|Levels used to guess how far a price may pull back before continuing its trend.|Traders watch the 38.2% and 61.8% levels.
Stochastic oscillator|Technical|An indicator showing where the price closed within its recent range.|Used to spot overbought and oversold zones.
Average true range|Technical|An indicator showing the average size of daily price swings.|Used to set stop-loss distances.
ADX|Technical|Average directional index: measures how strong a trend is, not its direction.|A reading above 25 suggests a strong trend.
On-balance volume|Technical|An indicator adding volume on up days and subtracting it on down days.|Rising OBV with rising price confirms a trend.
VWAP|Technical|Volume-weighted average price: the day's average price weighted by how much traded at each level.|Institutions often use VWAP as a fair-price benchmark.
Pivot points|Technical|Levels calculated from the previous day's prices to guess support and resistance.|Day traders mark them on the chart.
Head and shoulders|Technical|A chart pattern with three peaks, the middle highest, that often signals a trend reversal.|It can warn of the end of an uptrend.
Double top|Technical|A pattern where the price hits the same high twice and then falls.|It suggests buyers have run out of steam.
Double bottom|Technical|A pattern where the price hits the same low twice and then rises.|It suggests sellers are exhausted.
Cup and handle|Technical|A rounded bottom followed by a small dip, often seen before an upward breakout.|The shape resembles a tea cup.
Ascending triangle|Technical|A pattern with a flat top and rising lows that often ends in a breakout upward.|Buyers keep pushing against one resistance line.
Doji|Technical|A candle with almost equal open and close, showing indecision.|Neither buyers nor sellers won the day.
Hammer candle|Technical|A candle with a small body and long lower shadow after a fall, hinting at a bounce.|Buyers rejected the lower prices.
Engulfing pattern|Technical|A candle that fully covers the previous candle, hinting at a reversal.|A big green candle swallowing a small red one.
Golden cross|Technical|When a short-term moving average rises above a long-term one, seen as bullish.|The 50-day average crossing above the 200-day.
Death cross|Technical|When a short-term moving average falls below a long-term one, seen as bearish.|The 50-day average crossing below the 200-day.
Overbought|Technical|A condition when a price has risen so fast that a pullback may be near.|RSI above 70.
Oversold|Technical|A condition when a price has fallen so fast that a bounce may be near.|RSI below 30.
Divergence|Technical|When price and an indicator move in opposite directions, hinting at a trend change.|Price makes a new high but RSI does not.
Consolidation|Technical|A period when the price moves sideways in a narrow range.|It often comes before a breakout.
Range-bound market|Technical|A market that moves between a fixed floor and ceiling without a clear trend.|The Nifty stays between 22,000 and 22,500 for weeks.
Whipsaw|Technical|A sudden price move one way followed by a quick reversal that traps traders.|A false breakout that reverses at once.
Backtesting|Technical|Testing a trading idea on past data to see how it would have performed.|Checking a strategy on ten years of prices.
Risk-reward ratio|Risk|The amount you could lose compared with the amount you aim to gain.|Risking Rs 100 to make Rs 300 is a 1:3 ratio.
Position sizing|Risk|Deciding how much money to put in one trade based on how much you can afford to lose.|Risking only 1% of your capital per trade.
Drawdown|Risk|The fall from a portfolio's peak value to its lowest point afterwards.|A fall from Rs 10 lakh to Rs 8 lakh is a 20% drawdown.
Slippage|Trading|The difference between the price you expected and the price you actually got.|You expected Rs 100 but were filled at Rs 100.30.
Algorithmic trading|Trading|Using computer programs to place trades automatically by set rules.|A program buys when a moving average crossover occurs.
High-frequency trading|Trading|Ultra-fast computer trading that makes thousands of tiny trades in a blink.|Firms profit from tiny price gaps lasting milliseconds.
Market maker|Trading|A firm that constantly quotes buy and sell prices so others can always trade.|They earn the small gap between bid and ask.
Order book|Trading|A live list of all waiting buy and sell orders for a share.|It shows how many buyers and sellers sit at each price.
Market depth|Trading|The quantity of buy and sell orders waiting at different prices.|Shows how easily a big order can be absorbed.
Tick size|Trading|The smallest amount by which a price can move.|Most shares move in steps of 5 paise.
Cover order|Trading|An order that comes with a compulsory stop-loss for lower margin.|You enter a trade with a built-in stop-loss.
Bracket order|Trading|An order that sets your entry, target and stop-loss at once.|Buy at 100, target 105, stop-loss 97.
GTT order|Trading|Good till triggered: an order that waits up to a year until your set price is hit.|You set a buy trigger at Rs 90 and forget about it.
After-market order|Trading|An order placed after the market closes, to be sent when it opens next.|Placed at night and executed at the next morning's open.
Iceberg order|Trading|A large order split into small visible pieces so it does not scare the market.|Only a small part of the real size shows.
Immediate or cancel|Trading|An order that fills whatever it can right away and cancels the rest.|You ask for 500 shares and get 300; the rest is cancelled.
Basket order|Trading|A group of buy or sell orders placed together in one click.|Buying several shares of a theme at once.
Paper trading|Trading|Practising trading with pretend money to learn without risk.|You test a strategy on a simulator.
Trading journal|Trading|A record of your trades and the reasons behind them, used to learn from mistakes.|You note why you bought and what happened.
Black-Scholes model|Derivatives|A famous formula for working out the fair price of an option.|Uses price, strike, time, volatility and interest rate.
Volatility smile|Derivatives|A pattern where far-away strike options have higher implied volatility than at-the-money ones.|The curve of implied volatility looks like a smile.
Naked option selling|Derivatives|Selling options without holding any protection, which risks very large losses.|It can lose far more than the premium collected.
Calendar spread|Derivatives|Buying and selling options of the same strike but different expiry dates.|Used to profit from time decay differences.
Lot (F&O)|Derivatives|The fixed number of units in one futures or options contract.|One Nifty lot may cover a fixed set of index units.
Contract note|Trading|A document from your broker listing every trade, price, and charge of the day.|Check it for brokerage and taxes charged.
Brokerage|Trading|The fee a broker charges for executing your trades.|A flat fee per order at discount brokers.
Securities transaction tax|Trading|A small tax charged on buying or selling shares on an exchange.|Added to your trading costs automatically.
Stamp duty|Trading|A government charge collected when you buy shares or sign certain documents.|Deducted on the buy side of trades.
Depository participant|Trading|An agency, often your broker or bank, that holds your demat account.|Zerodha or HDFC Bank can be your DP.
Short covering|Trading|Buying back shares you sold short to close the position.|Short covering can push a price up quickly.
Hedge ratio|Derivatives|How much of a position is protected by an offsetting hedge.|Hedging half your shares gives a 0.5 ratio.
Basis|Derivatives|The difference between the spot price and the futures price.|A futures price above spot shows positive basis.
Cost of carry|Derivatives|The cost of holding an asset until a futures contract ends, mainly interest.|It explains why futures usually trade above spot.
Cash reserve ratio|Banking|The share of deposits that banks must keep as cash with the RBI.|A 4% CRR means Rs 4 of every Rs 100 deposit stays with the RBI.
Statutory liquidity ratio|Banking|The share of deposits banks must keep in safe, liquid assets such as government securities.|Banks park part of deposits in G-Secs and gold.
Reverse repo rate|Banking|The rate at which the RBI borrows money from banks.|Banks earn this rate when they park surplus cash with the RBI.
MCLR|Banking|Marginal cost of funds based lending rate: the minimum rate set by a bank for loans.|Older home loans are often linked to MCLR.
External benchmark lending rate|Banking|A loan rate linked to an outside benchmark such as the repo rate.|When the repo rate falls, your EBLR loan gets cheaper.
Marginal standing facility|Banking|An emergency borrowing window where banks borrow overnight from the RBI at a higher rate.|Used when banks are short of cash.
Bank rate|Banking|The rate at which the RBI lends long-term to banks, used as a policy signal.|It is usually higher than the repo rate.
Open market operations|Banking|The RBI buying or selling government bonds to add or drain money from the system.|Buying bonds puts more cash in the market.
Liquidity adjustment facility|Banking|The RBI's daily window for banks to borrow or park short-term money.|Repo and reverse repo come under this.
Net interest margin|Banking|The gap between what a bank earns on loans and pays on deposits, relative to its assets.|Higher margins mean the bank earns more on its lending.
Gross NPA|Banking|The total loans on which borrowers have stopped paying, before provisions.|A bank with Rs 100 crore bad loans out of Rs 2,000 crore has a 5% gross NPA.
Net NPA|Banking|Bad loans left after the bank has set aside money for them.|Lower than gross NPA.
Provision coverage ratio|Banking|The share of bad loans a bank has already set aside money to cover.|A 75% ratio means three-quarters of bad loans are covered.
Capital adequacy ratio|Banking|A bank's own capital compared with its risky assets, showing how safe it is.|Banks must keep this above the minimum set by the RBI.
Tier 1 capital|Banking|A bank's core capital, mainly equity, that absorbs losses first.|Higher Tier 1 means a stronger bank.
Basel norms|Banking|International rules that tell banks how much capital to hold.|Basel III came after the 2008 crisis.
Credit-deposit ratio|Banking|Loans a bank has given compared with deposits it has collected.|A 75% ratio means Rs 75 lent out of every Rs 100 deposit.
Priority sector lending|Banking|A rule that banks must lend a set share to areas like farming and small business.|Loans to farmers count under it.
Microfinance|Banking|Very small loans given to poor people and small businesses.|A Rs 20,000 loan to a woman starting a tailoring shop.
NBFC|Banking|A non-banking finance company that lends but cannot take regular deposits like a bank.|Bajaj Finance is an NBFC.
Payments bank|Banking|A bank that accepts deposits and offers payments but cannot give loans.|Paytm Payments Bank was one.
Small finance bank|Banking|A bank focusing on small borrowers and local savers.|Serves people underserved by large banks.
UPI|Banking|Unified Payments Interface: an instant mobile payment system run by NPCI.|Scanning a QR code to pay a shopkeeper.
NEFT|Banking|National Electronic Funds Transfer: bank transfers settled in batches.|Used for non-urgent transfers.
RTGS|Banking|Real-time gross settlement: instant bank transfers for large amounts.|Used for payments of Rs 2 lakh or more.
IMPS|Banking|Immediate Payment Service: instant transfers that work all day, every day.|Sending money late at night.
Fixed deposit|Banking|Money locked with a bank for a fixed period at a fixed interest rate.|You lock Rs 1 lakh for 2 years at 7%.
Recurring deposit|Banking|Saving a fixed amount every month for a set period at a fixed rate.|You deposit Rs 2,000 a month for a year.
Overdraft|Banking|Letting you withdraw more than you have in your account, up to a limit, with interest.|A business covers a short cash gap.
CIBIL score|Banking|A three-digit number showing how reliable you are at repaying loans.|A score above 750 helps you get cheaper loans.
Collateral|Banking|Something valuable you pledge to a lender as security for a loan.|Your house for a home loan.
Haircut|Banking|The reduction applied to the value of collateral or a claim.|A lender accepts Rs 80 against Rs 100 of assets.
Insolvency and Bankruptcy Code|Regulation|India's law for resolving companies that cannot repay debts within a set time.|Creditors can take a failed company through a resolution process.
NCLT|Regulation|National Company Law Tribunal: the court that handles company disputes and insolvency cases.|A bankrupt company's case is heard here.
Write-off|Banking|When a bank removes a bad loan from its books because recovery is unlikely.|The loan still may be recovered later.
Loan restructuring|Banking|Changing a loan's terms, such as extending its time, to help a struggling borrower.|Longer repayment time with a lower EMI.
Moratorium|Banking|A temporary pause on loan repayments.|EMIs paused for three months.
KYC|Regulation|Know your customer: verifying your identity before you open an account.|You submit Aadhaar and PAN.
Digital rupee|Banking|A digital form of the Indian rupee issued by the RBI.|Works like cash but in digital form.
GDP growth|Economy|How fast the total output of a country is increasing.|GDP growth of 7% means the economy produced 7% more.
Consumer price index|Economy|A measure of how the price of everyday goods and services changes for households.|The main inflation measure the RBI watches.
Wholesale price index|Economy|A measure of how prices change at the wholesale level, before reaching consumers.|Rises in WPI often feed into retail prices later.
Core inflation|Economy|Inflation excluding food and fuel, which swing a lot.|Shows the underlying price trend.
Deflation|Economy|A fall in the general price level over time.|Prices drop and people delay purchases.
Stagflation|Economy|Slow growth and rising prices together.|Unemployment is high while prices keep climbing.
Recession|Economy|A long period when the economy shrinks, often shown by two quarters of falling GDP.|Jobs get scarce and spending drops.
Fiscal deficit|Economy|The gap between what the government spends and what it earns, excluding borrowing.|Spending Rs 50 lakh crore against Rs 45 lakh crore income.
Current account deficit|Economy|When a country pays more to the world than it earns from it in goods, services and transfers.|India imports more than it exports.
Trade deficit|Economy|When a country imports more goods than it exports.|Buying Rs 100 of goods and selling only Rs 70.
Balance of payments|Economy|A record of all money coming into and going out of a country.|Covers trade, services and investments.
Forex reserves|Economy|Foreign currency and gold held by the central bank.|The RBI uses them to steady the rupee.
Rupee depreciation|Economy|A fall in the rupee's value against another currency.|Rs 83 per dollar becoming Rs 85.
Exchange rate|Economy|The price of one currency in terms of another.|Rs 85 for 1 US dollar.
Purchasing power parity|Economy|The idea that the same basket of goods should cost the same everywhere after currency conversion.|Used to compare living costs across countries.
Real interest rate|Economy|The interest rate after subtracting inflation.|7% interest with 5% inflation gives 2%.
Yield curve|Economy|A line showing bond yields from short to long maturities.|Normally slopes upward.
Inverted yield curve|Economy|When short-term yields are higher than long-term yields, often a recession warning.|It signals investors expect slower growth.
Quantitative easing|Economy|A central bank creating money to buy bonds and push interest rates down.|Used when rates are already near zero.
Quantitative tightening|Economy|A central bank shrinking its holdings of bonds, pulling money out of the system.|The opposite of quantitative easing.
Tapering|Economy|Gradually reducing a central bank's bond buying.|Markets often react nervously to tapering.
Soft landing|Economy|Slowing inflation without causing a recession.|Rates rise and growth cools but jobs hold up.
Business cycle|Economy|The repeated pattern of boom, slowdown, bust and recovery in an economy.|Growth peaks, falls, then recovers.
PMI|Economy|Purchasing managers' index: a survey where above 50 means business is expanding.|A PMI of 56 signals strong growth.
Index of Industrial Production|Economy|A measure of how much India's factories, mines and power plants are producing.|Released monthly.
GST collections|Economy|The monthly tax revenue the government gets from GST.|Rising collections often signal strong spending.
Disinvestment|Economy|When the government sells its stake in a public sector company.|Selling a part of a state-owned company's shares.
Subsidy|Economy|Government help that makes something cheaper for people or businesses.|A fertiliser subsidy lowers farmers' costs.
Direct tax|Economy|A tax paid directly by a person or company to the government.|Income tax is a direct tax.
Indirect tax|Economy|A tax added to the price of goods and services.|GST is an indirect tax.
Union Budget|Economy|The government's yearly plan showing expected income and spending.|Presented in Parliament every February.
FRBM Act|Regulation|A law that sets limits on the government's deficit and debt.|Pushes the government towards fiscal discipline.
Sovereign credit rating|Economy|A grade given to a country showing how likely it is to repay its debts.|A higher rating lowers borrowing costs.
Foreign direct investment|Economy|A foreign company investing directly in a business or factory in India.|A foreign carmaker setting up a plant.
Hot money|Economy|Short-term foreign money that can enter and leave a country very fast.|Sudden exits can hurt the rupee.
Capital controls|Economy|Rules that limit how freely money can move in or out of a country.|Limits on foreign investment.
IRDAI|Regulation|The insurance regulator of India.|It sets rules for insurers.
PFRDA|Regulation|The regulator for pension funds including the NPS.|It oversees retirement savings products.
Takeover code|Regulation|SEBI rules that govern when and how a company can be acquired.|Triggers an open offer above a set stake.
Open offer|Regulation|An offer to public shareholders to buy their shares after a big stake changes hands.|Required after an acquirer crosses 25%.
Corporate governance|Regulation|The rules and practices by which a company is directed and controlled.|Independent boards and honest reporting.
Independent director|Regulation|A board member with no close ties to the company, who watches over management.|Protects minority shareholders.
Shareholder activism|Regulation|When investors use their votes to push a company to change.|A fund demands a new board.
Proxy advisory firm|Regulation|A firm that advises big investors how to vote at company meetings.|IiAS advises Indian institutions.
ESG|Regulation|Environmental, social and governance factors used to judge how responsibly a company operates.|Funds may avoid companies with bad ESG scores.
Greenwashing|Regulation|A company falsely claiming to be more eco-friendly than it is.|Marketing a product as green with little proof.
Rupee convertibility|Economy|How freely the rupee can be exchanged for other currencies.|The rupee is fully convertible only on the current account.
Trade surplus|Economy|When a country exports more goods than it imports.|Selling Rs 120 of goods and buying Rs 100.
Repo market|Banking|A market where short-term loans are made against government securities.|Banks borrow cash using bonds as security.
Call money market|Banking|A market where banks lend each other money for very short periods.|Overnight loans between banks.
Treasury operations|Banking|A bank's activity of managing its own investments, cash and foreign exchange.|Buying bonds to earn interest on spare funds.
Fiscal stimulus|Economy|Government spending or tax cuts used to boost a slow economy.|A big infrastructure spending push.
Austerity|Economy|Government cuts in spending to reduce debt.|Cutting subsidies and pay raises.
Unemployment rate|Economy|The share of people who want work but cannot find it.|A 7% rate means 7 of every 100 jobseekers are jobless.
Gini coefficient|Economy|A number showing how unequally income is shared in a country.|Zero is perfect equality.
Per capita income|Economy|The average income per person in a country.|National income divided by population.
Bond|Fixed income|A loan you give to a government or company in return for regular interest and your money back later.|You lend Rs 10,000 for 5 years and get interest each year.
Coupon rate|Fixed income|The fixed yearly interest a bond pays, as a percentage of its face value.|A 7% coupon on a Rs 1,000 bond pays Rs 70 a year.
Yield to maturity|Fixed income|The total yearly return you earn if you buy a bond today and hold it until it matures.|Includes interest and any gain or loss on price.
Current yield|Fixed income|A bond's yearly interest divided by its current market price.|Rs 70 interest on a bond priced at Rs 950.
Maturity date|Fixed income|The date when a bond ends and the lender gets the face value back.|A 10-year bond issued today matures in 10 years.
Credit rating|Fixed income|A grade showing how likely a borrower is to repay its debts.|AAA is the safest and D means default.
Investment grade|Fixed income|Bonds rated high enough to be seen as relatively safe.|Rated BBB or above.
High-yield bond|Fixed income|A bond from a riskier borrower that pays higher interest to attract buyers.|Pays more but may default.
Government security|Fixed income|A bond issued by the government, seen as the safest investment.|A 10-year G-Sec pays a fixed coupon.
Treasury bill|Fixed income|A very short-term government security sold at a discount.|Buy at Rs 98 and get Rs 100 after 91 days.
Corporate bond|Fixed income|A bond issued by a company to raise money.|A company borrows from investors at 9%.
Zero-coupon bond|Fixed income|A bond that pays no interest but is sold at a deep discount and repaid at full value.|Buy for Rs 600 and receive Rs 1,000 at maturity.
Convertible bond|Fixed income|A bond that can be converted into the company's shares.|Gives interest now and a chance to own shares later.
Callable bond|Fixed income|A bond the issuer can repay early before its maturity date.|Issuers call bonds when interest rates fall.
Duration|Fixed income|A measure of how sensitive a bond's price is to changes in interest rates.|Higher duration means bigger price swings.
Interest rate risk|Fixed income|The risk that bond prices fall when interest rates rise.|Old 6% bonds lose value when new bonds pay 8%.
Credit risk|Fixed income|The risk that a borrower fails to repay what it owes.|A company misses a bond payment.
Perpetual bond|Fixed income|A bond with no maturity date that pays interest indefinitely.|The issuer may repay it only at its own choice.
AT1 bond|Fixed income|A risky bond issued by banks that can be written off if the bank is in trouble.|Pays higher interest but can lose everything.
Commercial paper|Fixed income|A short-term borrowing instrument issued by large companies.|A firm borrows for 90 days.
Certificate of deposit|Fixed income|A short-term deposit certificate issued by banks to raise money.|Used by banks to raise funds from the market.
Money market|Fixed income|The market for very short-term borrowing and lending, up to a year.|Treasury bills and commercial paper trade here.
Mutual fund|Funds|A pool of many investors' money managed by a professional to buy shares, bonds or other assets.|You hold units of a fund instead of picking shares.
NAV|Funds|Net asset value: the price of one unit of a mutual fund.|A fund with assets of Rs 100 crore and 10 crore units has NAV Rs 10.
Expense ratio|Funds|The yearly fee a fund charges, as a percentage of your money.|A 1% expense ratio costs Rs 1,000 a year on Rs 1 lakh.
Exit load|Funds|A fee charged if you withdraw from a fund too soon.|1% fee if you sell within a year.
SIP|Funds|Systematic investment plan: investing a fixed amount in a fund at regular intervals.|Rs 3,000 goes in on the 5th of every month.
SWP|Funds|Systematic withdrawal plan: taking a fixed amount out of a fund regularly.|Useful for a monthly income in retirement.
STP|Funds|Systematic transfer plan: moving money regularly from one fund to another.|Moving Rs 10,000 a month from a debt fund to an equity fund.
ELSS|Funds|Equity linked savings scheme: a mutual fund with tax benefits and a three-year lock-in.|You invest to save tax under the old regime.
Index fund|Funds|A fund that simply copies an index rather than picking shares.|A Nifty 50 index fund holds the same 50 shares.
ETF|Funds|Exchange traded fund: a fund that trades on the exchange like a share.|Buy a gold ETF through your demat account.
Fund manager|Funds|The professional who decides what a mutual fund buys and sells.|Aims to beat the benchmark.
Assets under management|Funds|The total money a fund or fund house manages for investors.|A fund house with Rs 5 lakh crore AUM.
Direct plan|Funds|A mutual fund option bought straight from the fund house with a lower expense ratio.|Cheaper because no distributor commission is paid.
Regular plan|Funds|A mutual fund option bought through a distributor, with a higher expense ratio.|The distributor earns a commission.
Growth option|Funds|A fund option that keeps profits invested instead of paying them out.|The NAV keeps compounding.
IDCW option|Funds|Income distribution cum capital withdrawal: a fund option that pays out money periodically.|The payout reduces the NAV.
Liquid fund|Funds|A debt fund that invests in very short-term instruments for safe parking of cash.|Used for money you may need soon.
Debt fund|Funds|A mutual fund that invests in bonds and other fixed-income instruments.|Usually less risky than equity funds.
Hybrid fund|Funds|A fund that invests in both shares and bonds.|65% equity and 35% debt.
Sectoral fund|Funds|A fund that invests only in one industry.|A banking fund or a pharma fund.
Thematic fund|Funds|A fund built around an idea such as consumption or green energy.|A fund that invests in electric vehicles.
Fund of funds|Funds|A fund that invests in other funds instead of directly in shares.|Used to invest in international funds.
Tracking error|Funds|How far an index fund's returns stray from its index.|A low tracking error means a closer copy.
Alpha|Funds|The extra return a fund earns over its benchmark after adjusting for risk.|Alpha of 2% means it beat the benchmark by 2%.
Sharpe ratio|Risk|Return earned per unit of risk taken; higher is better.|A fund with a higher Sharpe ratio rewarded risk better.
Standard deviation|Risk|A measure of how widely returns swing around their average.|A higher number means a bumpier ride.
Beta|Risk|How much a share tends to move compared with the whole market.|A beta of 1.5 means it moves about 1.5 times the market.
Riskometer|Funds|A meter on every mutual fund showing how risky it is, from low to very high.|Check it before investing.
Emergency fund|Personal finance|Money kept aside for surprise costs, usually 3 to 6 months of expenses.|Rs 1.5 lakh if you spend Rs 30,000 a month.
Net worth|Personal finance|Everything you own minus everything you owe.|Assets of Rs 20 lakh and loans of Rs 5 lakh give Rs 15 lakh.
50-30-20 rule|Personal finance|A budget plan: 50% needs, 30% wants and 20% savings.|On Rs 40,000, save Rs 8,000.
Compound interest|Personal finance|Interest earned on both your original money and the interest it already earned.|Rs 1,000 at 10% grows to Rs 1,210 in two years.
CAGR|Personal finance|Compound annual growth rate: the steady yearly rate at which something grew.|Rs 100 growing to Rs 200 in 5 years is about 14.9% CAGR.
XIRR|Personal finance|A yearly return measure for investments made on different dates, such as SIPs.|Used to see the true return of an SIP.
Absolute return|Personal finance|The total gain over a period without adjusting for time.|Rs 100 turning into Rs 130 is a 30% absolute return.
Credit utilisation|Personal finance|The share of your credit card limit that you are using.|Using Rs 30,000 of a Rs 1 lakh limit is 30%.
EMI|Personal finance|Equated monthly instalment: the fixed amount you pay each month to repay a loan.|Rs 20,000 a month for a home loan.
Loan prepayment|Personal finance|Paying back part or all of a loan earlier than scheduled.|Using a bonus to cut your home loan.
Loan-to-value ratio|Personal finance|The loan amount as a share of the value of the asset you are buying.|A Rs 40 lakh loan on a Rs 50 lakh home is 80%.
NPS|Personal finance|National Pension System: a government-backed retirement savings scheme.|You invest monthly and get a pension after 60.
EPF|Personal finance|Employees' Provident Fund: a retirement savings scheme where you and your employer contribute.|12% of basic pay goes in every month.
PPF|Personal finance|Public Provident Fund: a 15-year government savings scheme with tax-free interest.|You invest up to a yearly limit.
Sukanya Samriddhi Yojana|Personal finance|A government savings scheme for the girl child with high interest and tax benefits.|A parent opens an account for a daughter.
Annuity|Personal finance|A product that pays you a regular income, usually after retirement.|You pay a lump sum and get monthly payments for life.
Retirement corpus|Personal finance|The total money you need saved to live comfortably after you stop working.|Enough to cover expenses for 25 or more years.
FIRE movement|Personal finance|Financial independence, retire early: saving aggressively to stop working young.|Saving 50% of income for 15 years.
Term insurance|Insurance|A life cover that pays your family a lump sum if you die during the policy term.|Rs 1 crore cover for a small yearly premium.
Health insurance|Insurance|A policy that pays your hospital bills up to a limit.|Rs 5 lakh cover for the family.
Insurance premium|Insurance|The amount you pay to the insurer to keep your policy active.|Rs 12,000 a year for a health policy.
Sum assured|Insurance|The fixed amount an insurer promises to pay on a claim.|A Rs 50 lakh sum assured.
Claim settlement ratio|Insurance|The share of claims an insurer has paid out.|A 98% ratio means 98 of 100 claims were paid.
Waiting period|Insurance|The time before certain health conditions are covered under a policy.|Pre-existing illness may be covered only after 2 or 3 years.
Insurance rider|Insurance|An optional add-on to a policy for extra cover, such as accident cover.|A critical illness rider on term insurance.
ULIP|Insurance|Unit linked insurance plan: a product mixing insurance and market investments.|Part of the premium buys a life cover and part goes into funds.
Endowment plan|Insurance|A policy that gives life cover and also pays a lump sum at maturity.|Low returns, so compare carefully.
Income tax slab|Tax|The income ranges that are taxed at different rates.|Higher income is taxed at higher rates.
New tax regime|Tax|An income tax system with lower rates but fewer deductions.|Choose it if you claim few deductions.
Old tax regime|Tax|An income tax system with higher rates but many deductions and exemptions.|Lets you claim 80C and HRA.
TDS|Tax|Tax deducted at source: tax cut by the payer before you receive the money.|Your employer deducts tax from your salary.
Advance tax|Tax|Tax paid in instalments during the year instead of at the end.|Paid by freelancers and traders in four instalments.
ITR|Tax|Income tax return: the yearly form you file to report your income and tax.|Most people file it by July.
Section 80C|Tax|A rule letting you deduct up to a set amount for specified savings, under the old regime.|Money in PPF or ELSS can reduce taxable income.
Standard deduction|Tax|A fixed amount subtracted from salary income before calculating tax.|Available without bills or proof.
HRA|Tax|House rent allowance: part of your salary that can reduce tax if you pay rent.|Claimed with rent receipts.
Long-term capital gain|Tax|Profit from selling an investment held for more than the set period, taxed at a lower rate.|Shares sold after holding for over a year.
Short-term capital gain|Tax|Profit from selling an investment held for a short time, taxed at a higher rate.|Shares sold within a year.
Tax-loss harvesting|Tax|Selling losing investments to cancel out taxable gains.|A Rs 20,000 loss offsets Rs 20,000 of profit.
Form 16|Tax|A certificate from your employer showing salary paid and tax deducted.|Needed to file your income tax return.
Annual information statement|Tax|A statement showing the income and transactions the tax department has on record for you.|Check it before filing your return.
Input tax credit|Tax|A GST rule that lets businesses subtract tax paid on purchases from tax collected on sales.|Prevents tax being charged on tax.
Inflation-adjusted return|Personal finance|Your investment return after subtracting inflation.|9% return with 6% inflation gives about 3% real gain.
Rule of 72|Personal finance|A shortcut to estimate how many years it takes money to double: 72 divided by the rate.|At 8%, money doubles in about 9 years.
Sinking fund|Personal finance|Money set aside regularly for a planned future expense.|Saving every month for a car purchase.
Lifestyle inflation|Personal finance|Spending more as your income rises, leaving no extra savings.|Upgrading your phone and car with every raise.
Pay yourself first|Personal finance|Saving money as soon as you are paid, before spending on anything else.|Auto-transfer to an SIP on salary day.
Credit card revolving|Personal finance|Carrying an unpaid card balance to the next month, which attracts high interest.|Interest can exceed 36% a year.
Balance transfer|Personal finance|Moving a loan to another lender offering a lower interest rate.|Shifting a home loan to save interest.
Joint account|Personal finance|A bank account shared by two or more people.|Spouses sharing household money.
Nominee|Personal finance|A person you name to receive your investment or account if something happens to you.|Add a nominee to every account.
Will|Personal finance|A legal document saying how your assets should be shared after you pass away.|It avoids family disputes.
Power of attorney|Personal finance|A legal paper letting someone act on your behalf.|You authorise a relative to handle a property sale.
Forex market|Global|The global market where currencies are traded against each other.|Trading dollars for rupees or euros for yen.
Currency pair|Global|Two currencies quoted together to show the price of one in terms of the other.|USD/INR shows how many rupees one dollar costs.
Pip|Global|The smallest standard price move in a currency pair.|A move from 1.1000 to 1.1001 is one pip.
Spot rate|Global|The exchange rate for an immediate currency trade.|Today's dollar rate at the bank.
Forward contract|Global|An agreement to exchange currency at a fixed rate on a future date.|An importer locks Rs 85 per dollar for three months.
Carry trade|Global|Borrowing in a low-interest currency to invest in a higher-interest one.|Borrow in yen and invest in higher-yield bonds elsewhere.
Safe-haven asset|Global|An investment that people buy when markets are scared, such as gold.|Gold often rises when stocks fall.
Reserve currency|Global|A currency held by many central banks for international trade, like the US dollar.|Oil is mostly priced in dollars.
Dollar index|Global|An index showing the US dollar's strength against a basket of major currencies.|A rising dollar index often pressures the rupee.
Federal funds rate|Global|The US central bank's key interest rate.|Its changes affect markets worldwide.
FOMC|Global|The US Federal Reserve committee that decides interest rates.|Markets watch its meeting outcomes closely.
WTI crude|Commodities|A US benchmark for the price of crude oil.|Often a few dollars cheaper than Brent.
OPEC+|Commodities|A group of oil-producing countries that coordinate how much oil to supply.|Output cuts can push oil prices higher.
Commodity futures|Commodities|Contracts to buy or sell goods like gold or crude oil on a future date.|Traded on MCX in India.
Bullion|Commodities|Gold or silver in bars or coins valued by weight and purity.|A 1 kg gold bar.
Gold ETF|Commodities|A fund that tracks the price of gold and trades like a share.|Own gold without storing it.
Sovereign Gold Bond|Commodities|A government security whose value follows gold prices and pays small interest.|Gold exposure without physical storage.
Base metals|Commodities|Common industrial metals such as copper, aluminium and zinc.|Copper demand signals factory activity.
Contango|Commodities|When futures prices are higher than the spot price.|Next month's oil costs more than today's.
Backwardation|Commodities|When futures prices are lower than the spot price.|Often signals tight supply right now.
Agri commodities|Commodities|Farm products traded as commodities, such as wheat, soybean and cotton.|Prices depend on weather and monsoons.
Strategic petroleum reserve|Commodities|Emergency stocks of crude oil held by a government.|Used to fight supply shocks.
Supply chain|Global|The network of firms and steps that bring a product from raw material to customer.|A chip shortage stops car production.
Trade war|Global|A fight between countries using tariffs and restrictions on each other's goods.|Two countries raising taxes on each other's imports.
Sanctions|Global|Penalties that one country places on another to pressure it.|Banning purchases of certain goods.
Free trade agreement|Global|A deal between countries to lower or remove taxes on traded goods.|Cheaper imports and easier exports.
WTO|Global|World Trade Organization: a body that sets rules for trade between countries.|Helps settle trade disputes.
IMF|Global|International Monetary Fund: an institution that lends to countries in financial trouble.|Gives loans with conditions.
World Bank|Global|An institution that lends to countries to fund development projects.|Funds roads, schools and power plants.
BRICS|Global|A group of large emerging economies, originally Brazil, Russia, India, China and South Africa.|Cooperate on trade and finance.
G20|Global|A forum of 19 major economies and the EU that discusses global economic policy.|Leaders meet each year.
SWIFT|Global|A network banks use to send secure payment messages across borders.|Excluding a bank from SWIFT blocks its international payments.
Emerging market|Global|A developing economy with fast growth and higher risk, such as India or Brazil.|Investors buy for growth but face currency swings.
Developed market|Global|A rich, mature economy with stable institutions, such as the US or Japan.|Lower growth but lower risk.
MSCI index|Global|A family of global indices used by big funds to decide where to invest.|India's weight in MSCI emerging markets affects foreign flows.
S&P 500|Global|An index of 500 large US companies, a key gauge of the US market.|Often used as a global benchmark.
Nasdaq|Global|A US exchange known for technology companies.|Home to many big tech firms.
Dow Jones|Global|An index of 30 large US companies.|One of the oldest market indices.
Nikkei 225|Global|Japan's main stock index.|Tracks 225 big Japanese companies.
Hang Seng|Global|The main stock index of Hong Kong.|A guide to Chinese and Hong Kong shares.
Wall Street|Global|The financial district of New York, used to mean the US stock market.|Wall Street fell overnight.
Dalal Street|Global|Mumbai's financial street, used to mean the Indian stock market.|Dalal Street rallied on Monday.
Black swan event|Risk|A rare, shocking event that is hard to predict and has huge effects.|A sudden pandemic crashing markets.
Systemic risk|Risk|The risk that one failure triggers a collapse of the whole financial system.|A big bank failing and spreading panic.
Contagion|Risk|When a crisis in one place spreads to others.|One country's market crash hurts neighbours.
Credit crunch|Risk|A sudden shortage of loans because banks stop lending.|Businesses cannot borrow even at high rates.
Liquidity crisis|Risk|When many borrowers cannot get cash quickly to meet their payments.|Markets freeze and sellers find no buyers.
Too big to fail|Risk|A firm so large that its collapse would damage the whole economy, so the government may rescue it.|Large banks in 2008.
Bailout|Risk|Financial rescue of a failing company or country, usually by the government.|A struggling airline is saved with public money.
Moral hazard|Risk|When people take more risk because someone else will bear the cost.|A bank takes wild bets expecting a rescue.
Counterparty risk|Risk|The risk that the other side of a deal fails to keep its promise.|A broker defaults on a trade.
Value at risk|Risk|An estimate of the most you might lose over a period at a certain confidence level.|A 1-day VaR of Rs 1 lakh at 95%.
Stress test|Risk|A check of how a bank or portfolio would hold up in a severe downturn.|Banks simulate a 20% fall in real estate.
Risk appetite|Risk|How much risk an investor or firm is willing to take.|A young investor may take more risk.
Risk tolerance|Risk|How much loss you can handle without panicking.|You stay calm through a 20% fall.
Risk-adjusted return|Risk|The return you earned compared with the amount of risk you took.|Two funds both earn 12% but one swings far less.
Correlation|Risk|How closely two investments move together.|Two bank shares often move almost together.
Tail risk|Risk|The risk of a rare, extreme loss at the far end of possible outcomes.|A crash far worse than normal fluctuations.
Hedge fund|Funds|A private fund for wealthy investors that uses advanced strategies to seek profit.|Often uses leverage and short selling.
Private equity|Funds|Funds that buy stakes in unlisted companies to improve and later sell them.|A fund buys a firm and sells it in 5 years.
Venture capital|Funds|Money invested in young startups with high growth potential and high risk.|A fund backs a new app company.
Angel investor|Funds|A wealthy individual who invests their own money in very early startups.|Funds a founder with just an idea.
Unicorn|Funds|A startup valued at over 1 billion US dollars.|A fast-growing app company hitting that value.
Funding round|Funds|A stage in which a startup raises money from investors, such as Series A.|A company raises Rs 50 crore in Series A.
Pre-money valuation|Funds|What a startup is valued at before new investment comes in.|Pre-money Rs 80 crore plus Rs 20 crore raised gives Rs 100 crore post-money.
Term sheet|Funds|A short document listing the main terms of an investment before the final deal.|Sets valuation and investor rights.
Cap table|Funds|A table showing who owns how much of a company.|Founders hold 60% and investors 40%.
Fintech|Fintech|Companies using technology to offer financial services like payments and lending.|Paying with a mobile app instead of cash.
Neobank|Fintech|A fully digital bank with no physical branches.|Accounts opened and managed on a phone.
Buy now pay later|Fintech|A short-term credit option that lets you buy now and pay in parts later.|Splitting a Rs 6,000 phone into three payments.
Robo-advisor|Fintech|An app that suggests or manages investments using algorithms.|It builds a portfolio from your risk profile.
Blockchain|Fintech|A shared digital record that many computers keep, hard to change once written.|Used to record transactions securely.
Cryptocurrency|Fintech|A digital currency that uses cryptography and is not controlled by a central bank.|Bitcoin is the best-known example.
Stablecoin|Fintech|A cryptocurrency designed to keep a steady value, often tied to the dollar.|One token aims to equal 1 US dollar.
Bitcoin halving|Fintech|An event that cuts the reward for creating new bitcoin in half about every four years.|It slows the creation of new coins.
Decentralised finance|Fintech|Financial services built on blockchains that run without banks or brokers.|Lending and borrowing through code.
Tokenisation|Fintech|Turning ownership of an asset into digital tokens on a blockchain.|A property split into digital shares.
Open banking|Fintech|Letting apps access your bank data, with your consent, to offer better services.|A budgeting app that reads your accounts.
FOMO|Behaviour|Fear of missing out: buying something just because everyone else is.|Chasing a share after it has already doubled.
Herd mentality|Behaviour|Following the crowd instead of doing your own thinking.|Everyone buys the same hot share.
Confirmation bias|Behaviour|Looking only for information that supports what you already believe.|Reading only positive news about a share you own.
Loss aversion|Behaviour|Feeling the pain of losing more strongly than the joy of an equal gain.|Holding on to a losing share to avoid admitting a loss.
Anchoring|Behaviour|Relying too much on the first number you saw, such as your buying price.|Refusing to sell below the price you paid.
Overconfidence|Behaviour|Believing you know more than you really do.|Trading too often after a few lucky wins.
Recency bias|Behaviour|Giving too much weight to recent events and assuming they will continue.|Expecting a rally to last forever.
Sunk cost fallacy|Behaviour|Continuing something because of money already spent.|Adding more money to a failing investment.
Disposition effect|Behaviour|Selling winners too early and holding losers too long.|Booking a small profit and ignoring a big loss.
Mental accounting|Behaviour|Treating money differently depending on where it came from.|Gambling a bonus but saving salary.
Gambler's fallacy|Behaviour|Believing that a streak must reverse because it has gone on for a while.|Thinking a share is due to bounce after many falls.
Fear and greed index|Behaviour|A gauge of whether investors are mostly scared or greedy.|Extreme greed can signal a market top.
Efficient market hypothesis|Theory|The idea that share prices already reflect all available information.|It suggests beating the market is very hard.
Random walk theory|Theory|The idea that price changes are unpredictable, like steps in random directions.|Past prices cannot predict future prices.
Modern portfolio theory|Theory|The idea that you can lower risk without lowering return by mixing different investments.|Combining shares and bonds smooths the ride.
Pecking order|Theory|The idea that firms prefer to fund projects first from profit, then debt, then new shares.|A company uses retained profit before borrowing.
Winner's curse|Theory|When the winning bidder in an auction overpays.|Paying too much for a company in a bidding war.
Underwriter|IPO|A bank that guarantees to sell a company's new shares and helps price the issue.|An investment bank agrees to buy unsold IPO shares.
Lock-in period|IPO|A time during which certain shareholders are not allowed to sell their shares after an IPO.|Pre-IPO investors may wait six months to sell.
Cut-off price|IPO|The final price at which an IPO is issued, chosen within the price band.|Retail investors can bid at the cut-off price to be sure of getting shares.
Diluted EPS|Valuation|Earnings per share counting all shares that could be created from options and convertibles.|Always equal to or lower than basic EPS.
Market-cap weighted index|Markets|An index where bigger companies have a bigger influence on its movement.|A large company moving 5% shifts the index more than a small one.
Equal-weight index|Markets|An index where every company has the same influence regardless of size.|Each of 50 shares counts for 2%.
Total return index|Markets|An index that includes dividends reinvested, not just price changes.|Shows the full return an investor would earn.
Factor investing|Strategy|Choosing investments based on traits such as value, quality or momentum.|A fund picks low-debt, high-profit companies.
Top-down investing|Strategy|Starting with the economy and sectors, then choosing companies.|You pick banking as a sector first, then the best bank.
Bottom-up investing|Strategy|Starting with a company's own strength, regardless of the wider economy.|You pick a great business first, then check the sector.
REIT|Funds|Real estate investment trust: a company that owns income-earning property and shares the rent with investors.|You own a small share of office buildings.
InvIT|Funds|Infrastructure investment trust: a trust that owns roads or power lines and passes on income.|Toll road income goes to unit holders.
Alternative investment fund|Funds|A privately pooled fund that invests in assets beyond regular shares and bonds.|Venture capital and hedge funds come under this.
Depositary receipt|Global|A certificate that lets investors trade shares of a foreign company on their local exchange.|An ADR lets US investors buy an Indian company.
Dual listing|Global|A company's shares being listed on two exchanges.|Listed on both NSE and BSE.
Value trap|Markets|A share that looks cheap but stays cheap because the business is weak.|A low P/E that never rises as profits keep shrinking.
Window dressing|Markets|Making accounts or portfolios look better just before a reporting date.|A fund buys winners at quarter-end to show them in its holdings.
Fiscal year|Accounting|The 12-month period a company or government uses for its accounts; in India April to March.|FY26 runs from April 2025 to March 2026.
Trailing twelve months|Analysis|The most recent 12 months of data, regardless of the financial year.|TTM profit adds the last four quarters.
Run rate|Analysis|A forecast of yearly performance by multiplying the latest period.|A Rs 10 crore month implies a Rs 120 crore run rate.
Burn rate|Analysis|How fast a company spends its cash, usually a startup with losses.|Spending Rs 2 crore a month.
Unit economics|Analysis|The profit or loss a company makes on each single unit sold or customer served.|Earning Rs 20 per order after costs.
EBITDA margin|Ratios|EBITDA as a percentage of revenue.|Rs 25 EBITDA on Rs 100 sales is a 25% margin.
Capacity utilisation|Analysis|How much of its production capacity a company is actually using.|A plant running at 80% of its maximum.
Same-store sales|Analysis|Sales growth from stores open for at least a year, excluding new ones.|Shows if existing stores are really growing.
Churn rate|Analysis|The share of customers who stop using a service in a period.|A 3% monthly churn means 3 of every 100 customers leave.
Gross merchandise value|Analysis|The total value of goods sold through a platform, before costs and returns.|An online marketplace's total sales.
Dividend trap|Markets|A very high dividend yield that exists only because the share price has crashed.|A 12% yield that the company cannot afford to keep paying.
Bad debt|Accounting|Money owed to a company that it does not expect to recover.|A customer who goes bankrupt before paying."""


def _load():
    items = []
    for line in _RAW.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 4 and all(parts):
            items.append({"term": parts[0], "cat": parts[1], "meaning": parts[2], "example": parts[3]})
    random.Random(2026).shuffle(items)
    return items


TERMS = _load()
