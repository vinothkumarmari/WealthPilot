"""
AI/ML Recommendation Engine for Money Management App
Provides intelligent financial suggestions based on user data
"""
import numpy as np
from datetime import datetime, timezone, timedelta
from .rate_monitor import SCHEME_RATES, PF_RATES, COMMODITY_BASE, GOVT_URLS


class FinancialAdvisor:
    """AI-powered financial advisor using rule-based + ML algorithms"""
    
    # 50-30-20 Rule thresholds
    NEEDS_RATIO = 0.50
    WANTS_RATIO = 0.30
    SAVINGS_RATIO = 0.20
    
    NEEDS_CATEGORIES = ['Housing', 'Food & Groceries', 'Transportation', 'Utilities', 'Healthcare', 'Insurance']
    WANTS_CATEGORIES = ['Entertainment', 'Shopping', 'Personal Care', 'Miscellaneous']
    SAVINGS_CATEGORIES = ['Savings', 'Investments', 'Debt Payments']
    
    def __init__(self):
        ppf_rate = SCHEME_RATES['PPF']['rate']
        epf_rate = PF_RATES['EPF']['rate']
        self.investment_options = {
            'Fixed Deposit': {'risk': 'low', 'return_range': (6.0, 7.5), 'min_tenure_years': 1, 'liquidity': 'low'},
            'Recurring Deposit': {'risk': 'low', 'return_range': (5.5, 7.0), 'min_tenure_years': 1, 'liquidity': 'low'},
            'PPF': {'risk': 'low', 'return_range': (ppf_rate, ppf_rate + 0.4), 'min_tenure_years': 15, 'liquidity': 'very_low'},
            'EPF': {'risk': 'low', 'return_range': (epf_rate, epf_rate + 0.25), 'min_tenure_years': 5, 'liquidity': 'very_low'},
            'NPS': {'risk': 'moderate', 'return_range': (9.0, 12.0), 'min_tenure_years': 20, 'liquidity': 'very_low'},
            'Gold': {'risk': 'low', 'return_range': (7.0, 10.0), 'min_tenure_years': 3, 'liquidity': 'high'},
            'Silver': {'risk': 'moderate', 'return_range': (5.0, 8.0), 'min_tenure_years': 3, 'liquidity': 'high'},
            'Mutual Funds (Equity)': {'risk': 'high', 'return_range': (10.0, 15.0), 'min_tenure_years': 5, 'liquidity': 'high'},
            'Mutual Funds (Debt)': {'risk': 'low', 'return_range': (6.0, 8.0), 'min_tenure_years': 3, 'liquidity': 'high'},
            'Mutual Funds (Hybrid)': {'risk': 'moderate', 'return_range': (8.0, 12.0), 'min_tenure_years': 3, 'liquidity': 'high'},
            'Index Funds': {'risk': 'moderate', 'return_range': (10.0, 14.0), 'min_tenure_years': 5, 'liquidity': 'high'},
            'Stocks (Blue Chip)': {'risk': 'moderate', 'return_range': (10.0, 16.0), 'min_tenure_years': 5, 'liquidity': 'very_high'},
            'Stocks (Mid Cap)': {'risk': 'high', 'return_range': (12.0, 20.0), 'min_tenure_years': 5, 'liquidity': 'very_high'},
            'Stocks (Small Cap)': {'risk': 'very_high', 'return_range': (15.0, 25.0), 'min_tenure_years': 7, 'liquidity': 'very_high'},
            'Real Estate': {'risk': 'moderate', 'return_range': (8.0, 12.0), 'min_tenure_years': 10, 'liquidity': 'very_low'},
            'REITs': {'risk': 'moderate', 'return_range': (7.0, 10.0), 'min_tenure_years': 3, 'liquidity': 'high'},
            'Sovereign Gold Bond': {'risk': 'low', 'return_range': (7.5, 10.5), 'min_tenure_years': 8, 'liquidity': 'moderate'},
            'Government Bonds': {'risk': 'low', 'return_range': (6.5, 7.5), 'min_tenure_years': 5, 'liquidity': 'moderate'},
            'Corporate Bonds': {'risk': 'moderate', 'return_range': (8.0, 10.0), 'min_tenure_years': 3, 'liquidity': 'moderate'},
            'SIP': {'risk': 'moderate', 'return_range': (10.0, 15.0), 'min_tenure_years': 5, 'liquidity': 'high'},
        }
    
    def analyze_financial_health(self, monthly_salary, total_expenses, total_investments, total_debts):
        """Calculate financial health score (0-100)"""
        if monthly_salary <= 0:
            return {'score': 0, 'grade': 'N/A', 'message': 'Please add your salary information',
                    'savings_rate': 0, 'investment_rate': 0, 'debt_ratio': 0, 'expense_ratio': 0}
        
        savings_rate = max(0, (monthly_salary - total_expenses) / monthly_salary) * 100
        investment_rate = (total_investments / (monthly_salary * 12)) * 100 if monthly_salary > 0 else 0
        debt_ratio = (total_debts / (monthly_salary * 12)) * 100 if monthly_salary > 0 else 0
        
        # Scoring algorithm
        score = 0
        
        # Savings rate score (max 30 points)
        if savings_rate >= 30: score += 30
        elif savings_rate >= 20: score += 25
        elif savings_rate >= 10: score += 15
        elif savings_rate > 0: score += 5
        
        # Investment score (max 30 points)
        if investment_rate >= 25: score += 30
        elif investment_rate >= 15: score += 25
        elif investment_rate >= 10: score += 15
        elif investment_rate > 0: score += 5
        
        # Low debt score (max 20 points)
        if debt_ratio == 0: score += 20
        elif debt_ratio < 20: score += 15
        elif debt_ratio < 40: score += 10
        elif debt_ratio < 60: score += 5
        
        # Expense management (max 20 points)
        expense_ratio = (total_expenses / monthly_salary) * 100 if monthly_salary > 0 else 100
        if expense_ratio <= 50: score += 20
        elif expense_ratio <= 70: score += 15
        elif expense_ratio <= 85: score += 10
        elif expense_ratio < 100: score += 5
        
        # Grade assignment
        if score >= 85: grade = 'A+'
        elif score >= 75: grade = 'A'
        elif score >= 65: grade = 'B+'
        elif score >= 55: grade = 'B'
        elif score >= 45: grade = 'C+'
        elif score >= 35: grade = 'C'
        else: grade = 'D'
        
        messages = {
            'A+': 'Excellent! Your finances are in great shape. Keep it up!',
            'A': 'Very Good! You are managing your money well.',
            'B+': 'Good! Some room for improvement in savings/investments.',
            'B': 'Fair. Consider reducing expenses and increasing investments.',
            'C+': 'Below Average. You need to work on your financial planning.',
            'C': 'Poor. Urgent attention needed on expense management.',
            'D': 'Critical. Please seek financial guidance immediately.'
        }
        
        return {
            'score': score,
            'grade': grade,
            'message': messages[grade],
            'savings_rate': round(savings_rate, 1),
            'investment_rate': round(investment_rate, 1),
            'debt_ratio': round(debt_ratio, 1),
            'expense_ratio': round(expense_ratio, 1)
        }
    
    def get_budget_analysis(self, monthly_salary, expenses_by_category, ratios=None):
        """Analyze budget using customizable rule (default 50/30/20)"""
        needs_ratio = (ratios.get('needs', 50) / 100) if ratios else self.NEEDS_RATIO
        wants_ratio = (ratios.get('wants', 30) / 100) if ratios else self.WANTS_RATIO
        savings_ratio = (ratios.get('savings', 20) / 100) if ratios else self.SAVINGS_RATIO

        needs_total = sum(expenses_by_category.get(cat, 0) for cat in self.NEEDS_CATEGORIES)
        wants_total = sum(expenses_by_category.get(cat, 0) for cat in self.WANTS_CATEGORIES)
        savings_total = sum(expenses_by_category.get(cat, 0) for cat in self.SAVINGS_CATEGORIES)
        
        ideal_needs = monthly_salary * needs_ratio
        ideal_wants = monthly_salary * wants_ratio
        ideal_savings = monthly_salary * savings_ratio
        
        analysis = {
            'needs': {
                'actual': needs_total,
                'ideal': ideal_needs,
                'percentage': round((needs_total / monthly_salary * 100), 1) if monthly_salary > 0 else 0,
                'coverage': round((needs_total / ideal_needs * 100), 1) if ideal_needs > 0 else 0,
                'status': 'over' if needs_total > ideal_needs else 'under',
                'difference': abs(needs_total - ideal_needs)
            },
            'wants': {
                'actual': wants_total,
                'ideal': ideal_wants,
                'percentage': round((wants_total / monthly_salary * 100), 1) if monthly_salary > 0 else 0,
                'coverage': round((wants_total / ideal_wants * 100), 1) if ideal_wants > 0 else 0,
                'status': 'over' if wants_total > ideal_wants else 'under',
                'difference': abs(wants_total - ideal_wants)
            },
            'savings': {
                'actual': savings_total,
                'ideal': ideal_savings,
                'percentage': round((savings_total / monthly_salary * 100), 1) if monthly_salary > 0 else 0,
                'coverage': round((savings_total / ideal_savings * 100), 1) if ideal_savings > 0 else 0,
                'status': 'under' if savings_total < ideal_savings else 'over',
                'difference': abs(savings_total - ideal_savings)
            }
        }
        
        tips = []
        if needs_total > ideal_needs:
            tips.append(f"Your essential expenses are ₹{needs_total - ideal_needs:,.0f} over the recommended 50%. Consider renegotiating rent or switching utilities.")
        if wants_total > ideal_wants:
            tips.append(f"Discretionary spending is ₹{wants_total - ideal_wants:,.0f} over budget. Try cutting entertainment or shopping expenses.")
        if savings_total < ideal_savings:
            tips.append(f"You should save ₹{ideal_savings - savings_total:,.0f} more per month. Start a SIP or auto-transfer to savings.")
        if needs_total <= ideal_needs and wants_total <= ideal_wants and savings_total >= ideal_savings:
            tips.append("Great job! Your budget follows the 50/30/20 rule perfectly. Consider increasing investments.")
        
        analysis['tips'] = tips
        return analysis
    
    def get_investment_suggestions(self, monthly_salary, age, risk_appetite, existing_investments=None):
        """AI-powered investment suggestions based on user profile"""
        if existing_investments is None:
            existing_investments = []
            
        suggestions = []
        monthly_investable = monthly_salary * 0.20  # 20% of salary for investments
        # Keep recommendations practical even for low/unstable salary inputs.
        practical_min = 500

        def build_range(base_amount):
            low = max(practical_min, round(base_amount * 0.8, -1))
            high = max(low, round(base_amount * 1.2, -1))
            return int(low), int(high)
        
        risk_map = {
            'low': ['low'],
            'moderate': ['low', 'moderate'],
            'high': ['low', 'moderate', 'high', 'very_high']
        }
        acceptable_risks = risk_map.get(risk_appetite, ['low', 'moderate'])
        
        # Age-based allocation strategy
        equity_allocation = max(20, 100 - age)  # Classic rule: 100 - age = equity %
        debt_allocation = 100 - equity_allocation
        
        # Filter investments by risk appetite
        suitable = {}
        for name, details in self.investment_options.items():
            if details['risk'] in acceptable_risks:
                avg_return = np.mean(details['return_range'])
                suitable[name] = {**details, 'avg_return': avg_return}
        
        # Sort by average return
        sorted_investments = sorted(suitable.items(), key=lambda x: x[1]['avg_return'], reverse=True)
        
        # Generate portfolio suggestion
        existing_types = [inv.get('type', '') for inv in existing_investments] if existing_investments else []
        
        # Core suggestions
        if age < 30:
            sip_base = max(monthly_investable * 0.4, practical_min)
            sip_min, sip_max = build_range(sip_base)
            suggestions.append({
                'title': 'Start SIP in Index Funds',
                'description': f'At age {age}, you have time for compounding. Suggested SIP range: ₹{sip_min:,.0f} to ₹{sip_max:,.0f}/month in Nifty 50 Index Fund.',
                'amount': sip_base,
                'min_amount': sip_min,
                'max_amount': sip_max,
                'type': 'equity',
                'priority': 'high',
                'icon': 'trending_up',
            })
            efund = max(monthly_salary * 6, monthly_salary * 3)
            suggestions.append({
                'title': 'Emergency Fund in Liquid Fund',
                'description': f'Build an emergency fund target between 3-6 months expenses (₹{max(monthly_salary * 3, 0):,.0f} to ₹{max(monthly_salary * 6, 0):,.0f}).',
                'amount': efund,
                'min_amount': int(max(monthly_salary * 3, 0)),
                'max_amount': int(max(monthly_salary * 6, 0)),
                'type': 'safety',
                'priority': 'high',
                'icon': 'shield',
            })
            ppf_base = max(min(monthly_investable * 0.2, 12500), practical_min)
            ppf_min, ppf_max = build_range(ppf_base)
            suggestions.append({
                'title': 'PPF for Tax Saving + Growth',
                'description': f'Invest ₹{ppf_min:,.0f} to ₹{ppf_max:,.0f}/month in PPF for tax-efficient long-term growth.',
                'amount': ppf_base,
                'min_amount': ppf_min,
                'max_amount': ppf_max,
                'type': 'debt',
                'priority': 'medium',
                'icon': 'savings',
            })
        elif age < 45:
            mf_base = max(monthly_investable * 0.35, practical_min)
            mf_min, mf_max = build_range(mf_base)
            suggestions.append({
                'title': 'Diversified Mutual Fund SIP',
                'description': f'Invest ₹{mf_min:,.0f} to ₹{mf_max:,.0f}/month in Large+Mid Cap Hybrid Funds.',
                'amount': mf_base,
                'min_amount': mf_min,
                'max_amount': mf_max,
                'type': 'equity',
                'priority': 'high',
                'icon': 'trending_up',
            })
            nps_base = max(monthly_investable * 0.15, practical_min)
            nps_min, nps_max = build_range(nps_base)
            suggestions.append({
                'title': 'NPS for Retirement',
                'description': f'NPS contribution range: ₹{nps_min:,.0f} to ₹{nps_max:,.0f}/month for retirement + tax benefits.',
                'amount': nps_base,
                'min_amount': nps_min,
                'max_amount': nps_max,
                'type': 'retirement',
                'priority': 'high',
                'icon': 'elderly',
            })
        else:
            fd_base = max(monthly_investable * 0.3, practical_min)
            fd_min, fd_max = build_range(fd_base)
            suggestions.append({
                'title': 'Fixed Deposit Ladder',
                'description': f'Create FD ladder with ₹{fd_min:,.0f} to ₹{fd_max:,.0f}/month across 1-5 year terms.',
                'amount': fd_base,
                'min_amount': fd_min,
                'max_amount': fd_max,
                'type': 'debt',
                'priority': 'high',
                'icon': 'account_balance',
            })
            scss_base = max(monthly_investable * 0.25, practical_min)
            scss_min, scss_max = build_range(scss_base)
            suggestions.append({
                'title': 'Senior Citizen Savings Scheme',
                'description': f'SCSS contribution range: ₹{scss_min:,.0f} to ₹{scss_max:,.0f}/month equivalent for steady income.',
                'amount': scss_base,
                'min_amount': scss_min,
                'max_amount': scss_max,
                'type': 'debt',
                'priority': 'high',
                'icon': 'savings',
            })
        
        # Gold & Silver suggestions (for all ages)
        sgb_base = max(monthly_investable * 0.1, practical_min)
        sgb_min, sgb_max = build_range(sgb_base)
        suggestions.append({
            'title': 'Sovereign Gold Bond (SGB)',
            'description': f'SGB allocation range: ₹{sgb_min:,.0f} to ₹{sgb_max:,.0f}/month for gold exposure + 2.5% annual interest.',
            'amount': sgb_base,
            'min_amount': sgb_min,
            'max_amount': sgb_max,
            'type': 'commodity',
            'priority': 'medium',
            'icon': 'paid',
        })
        silver_base = max(monthly_investable * 0.05, practical_min)
        silver_min, silver_max = build_range(silver_base)
        suggestions.append({
            'title': 'Silver ETF',
            'description': f'Silver ETF range: ₹{silver_min:,.0f} to ₹{silver_max:,.0f}/month for diversification.',
            'amount': silver_base,
            'min_amount': silver_min,
            'max_amount': silver_max,
            'type': 'commodity',
            'priority': 'low',
            'icon': 'diamond',
        })
        
        # Available investment options table
        investment_table = []
        for name, details in sorted_investments[:10]:
            investment_table.append({
                'name': name,
                'risk': details['risk'],
                'return_min': details['return_range'][0],
                'return_max': details['return_range'][1],
                'avg_return': details['avg_return'],
                'min_tenure': details['min_tenure_years'],
                'liquidity': details['liquidity']
            })
        
        return {
            'suggestions': suggestions,
            'monthly_investable': monthly_investable,
            'equity_allocation': equity_allocation,
            'debt_allocation': debt_allocation,
            'investment_table': investment_table
        }
    
    def get_asset_buying_plan(self, monthly_salary, age, existing_emi_total=0):
        """Generate asset buying suggestions based on salary and age"""
        if monthly_salary <= 0:
            return {
                'monthly_salary': 0, 'max_emi_capacity': 0,
                'current_emi': existing_emi_total, 'available_for_new_emi': 0,
                'plans': []
            }
        annual_salary = monthly_salary * 12
        available_for_emi = (monthly_salary * 0.40) - existing_emi_total  # Max 40% for EMIs
        
        plans = []
        
        # Car suggestion
        car_budget = annual_salary * 0.5  # 50% of annual salary
        car_emi = self._calculate_emi(car_budget * 0.8, 8.5, 5)  # 80% loan, 8.5%, 5 years
        if car_emi <= available_for_emi:
            plans.append({
                'asset': 'Car',
                'icon': 'directions_car',
                'budget': car_budget,
                'down_payment': car_budget * 0.2,
                'loan_amount': car_budget * 0.8,
                'emi': car_emi,
                'tenure_years': 5,
                'interest_rate': 8.5,
                'affordable': True,
                'tip': f'Budget: ₹{car_budget:,.0f}. Save ₹{car_budget * 0.2:,.0f} for down payment over {int(car_budget * 0.2 / (monthly_salary * 0.1))} months.',
                'segments': self._get_car_segments(car_budget)
            })
        
        # Bike suggestion
        bike_budget = annual_salary * 0.15
        plans.append({
            'asset': 'Bike/Two-Wheeler',
            'icon': 'two_wheeler',
            'budget': bike_budget,
            'down_payment': bike_budget * 0.3,
            'loan_amount': bike_budget * 0.7,
            'emi': self._calculate_emi(bike_budget * 0.7, 9.0, 3),
            'tenure_years': 3,
            'interest_rate': 9.0,
            'affordable': True,
            'tip': f'A two-wheeler within ₹{bike_budget:,.0f} is comfortable for your salary.'
        })
        
        # House/Flat suggestion
        house_budget = annual_salary * 5  # 5x annual salary
        house_emi = self._calculate_emi(house_budget * 0.8, 8.5, 20)
        plans.append({
            'asset': 'House/Flat',
            'icon': 'home',
            'budget': house_budget,
            'down_payment': house_budget * 0.2,
            'loan_amount': house_budget * 0.8,
            'emi': house_emi,
            'tenure_years': 20,
            'interest_rate': 8.5,
            'affordable': house_emi <= available_for_emi,
            'tip': f'Target property: ₹{house_budget:,.0f}. Save ₹{house_budget * 0.2:,.0f} for down payment. EMI: ₹{house_emi:,.0f}/month.',
            'saving_months': int(house_budget * 0.2 / (monthly_salary * 0.15)) if monthly_salary > 0 else 0
        })
        
        # Land suggestion
        land_budget = annual_salary * 3
        plans.append({
            'asset': 'Land/Plot',
            'icon': 'landscape',
            'budget': land_budget,
            'down_payment': land_budget * 0.3,
            'loan_amount': land_budget * 0.7,
            'emi': self._calculate_emi(land_budget * 0.7, 9.5, 15),
            'tenure_years': 15,
            'interest_rate': 9.5,
            'affordable': self._calculate_emi(land_budget * 0.7, 9.5, 15) <= available_for_emi,
            'tip': f'Invest in land near growing cities. Budget: ₹{land_budget:,.0f}. Land appreciates 8-12% annually.'
        })
        
        # Farming Land
        farm_budget = annual_salary * 2
        plans.append({
            'asset': 'Farming Land',
            'icon': 'agriculture',
            'budget': farm_budget,
            'down_payment': farm_budget * 0.4,
            'loan_amount': farm_budget * 0.6,
            'emi': self._calculate_emi(farm_budget * 0.6, 7.0, 10),
            'tenure_years': 10,
            'interest_rate': 7.0,
            'affordable': True,
            'tip': f'Agricultural land with irrigation: ₹{farm_budget:,.0f}. Can generate ₹{farm_budget * 0.05:,.0f}/year rental income.',
            'benefits': ['Agricultural income is tax-free', 'Land value appreciation', 'Rental/crop income', 'Government subsidies available']
        })
        
        # Summary
        summary = {
            'monthly_salary': monthly_salary,
            'max_emi_capacity': monthly_salary * 0.40,
            'current_emi': existing_emi_total,
            'available_for_new_emi': available_for_emi,
            'plans': plans
        }
        
        return summary
    
    def get_commodity_suggestions(self, monthly_salary):
        """Gold, Silver, and other commodity investment suggestions"""
        monthly_investment = monthly_salary * 0.10  # 10% for commodities
        
        return [
            {
                'commodity': 'Gold',
                'icon': 'paid',
                'color': '#FFD700',
                'current_trend': 'Bullish',
                'annual_return': '8-12%',
                'options': [
                    {'name': 'Sovereign Gold Bond (SGB)', 'min_invest': 5000, 'benefit': 'Gold returns + 2.5% annual interest, tax free on maturity', 'apply_url': 'https://www.rbi.org.in/Scripts/Faqsgoldbond.aspx'},
                    {'name': 'Gold ETF', 'min_invest': 1000, 'benefit': 'High liquidity, no storage hassle, tracks gold price', 'apply_url': 'https://www.mutualfundssahihai.com/en'},
                    {'name': 'Digital Gold', 'min_invest': 100, 'benefit': 'Start with as low as ₹100, 24K purity guaranteed', 'apply_url': 'https://www.paytmmoney.com/digital-gold'},
                    {'name': 'Gold Mutual Fund', 'min_invest': 500, 'benefit': 'SIP option available, professionally managed', 'apply_url': 'https://www.mutualfundssahihai.com/en'},
                ],
                'suggested_allocation': monthly_investment * 0.6,
                'tip': 'Gold is a hedge against inflation. Allocate 5-10% of portfolio.'
            },
            {
                'commodity': 'Silver',
                'icon': 'diamond',
                'color': '#C0C0C0',
                'current_trend': 'Moderate Bullish',
                'annual_return': '5-10%',
                'options': [
                    {'name': 'Silver ETF', 'min_invest': 1000, 'benefit': 'Easy to trade, no physical storage needed', 'apply_url': 'https://www.mutualfundssahihai.com/en'},
                    {'name': 'Silver Mutual Fund', 'min_invest': 500, 'benefit': 'SIP available, diversified silver exposure', 'apply_url': 'https://www.mutualfundssahihai.com/en'},
                    {'name': 'Physical Silver (Coins/Bars)', 'min_invest': 2000, 'benefit': 'Tangible asset, good for long term', 'apply_url': 'https://www.mmtcpamp.com/'},
                ],
                'suggested_allocation': monthly_investment * 0.3,
                'tip': 'Silver has industrial demand. Good for portfolio diversification.'
            },
            {
                'commodity': 'Other Commodities',
                'icon': 'inventory_2',
                'color': '#8B4513',
                'current_trend': 'Mixed',
                'annual_return': '5-15%',
                'options': [
                    {'name': 'Commodity Mutual Funds', 'min_invest': 500, 'benefit': 'Diversified commodity exposure', 'apply_url': 'https://www.mutualfundssahihai.com/en'},
                    {'name': 'Multi-Commodity ETF', 'min_invest': 1000, 'benefit': 'Covers gold, silver, crude, base metals', 'apply_url': 'https://www.mutualfundssahihai.com/en'},
                ],
                'suggested_allocation': monthly_investment * 0.1,
                'tip': 'Keep commodity allocation under 15% of total portfolio.'
            }
        ]
    
    def predict_expense_trend(self, expense_history):
        """Simple ML-based expense trend prediction using linear regression"""
        if len(expense_history) < 3:
            return {'prediction': None, 'trend': 'insufficient_data'}
        
        amounts = [e['amount'] for e in expense_history]
        x = np.arange(len(amounts)).reshape(-1, 1)
        y = np.array(amounts)
        
        # Simple linear regression
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        numerator = np.sum((x.flatten() - x_mean) * (y - y_mean))
        denominator = np.sum((x.flatten() - x_mean) ** 2)
        
        if denominator == 0:
            return {'prediction': y_mean, 'trend': 'stable'}
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Predict next month
        next_month = len(amounts)
        prediction = slope * next_month + intercept
        
        # Determine trend
        if slope > 50:
            trend = 'increasing'
            trend_icon = 'trending_up'
            trend_color = 'danger'
        elif slope < -50:
            trend = 'decreasing'
            trend_icon = 'trending_down'
            trend_color = 'success'
        else:
            trend = 'stable'
            trend_icon = 'trending_flat'
            trend_color = 'info'
        
        return {
            'prediction': max(0, round(prediction, 2)),
            'trend': trend,
            'trend_icon': trend_icon,
            'trend_color': trend_color,
            'slope': round(slope, 2),
            'avg_expense': round(np.mean(amounts), 2)
        }
    
    def calculate_retirement_corpus(self, current_age, retirement_age, monthly_expense, inflation_rate=6.0, return_rate=10.0):
        """Calculate required retirement corpus"""
        years_to_retire = retirement_age - current_age
        years_post_retirement = 85 - retirement_age  # Assume life expectancy 85
        
        # Future monthly expense at retirement
        future_expense = monthly_expense * ((1 + inflation_rate/100) ** years_to_retire)
        future_annual_expense = future_expense * 12
        
        # Required corpus (accounting for inflation post retirement)
        real_return = ((1 + return_rate/100) / (1 + inflation_rate/100)) - 1
        if real_return <= 0:
            corpus = future_annual_expense * years_post_retirement
        else:
            corpus = future_annual_expense * ((1 - (1 + real_return) ** (-years_post_retirement)) / real_return)
        
        # Monthly SIP needed
        monthly_rate = return_rate / 100 / 12
        months = years_to_retire * 12
        if monthly_rate > 0 and months > 0:
            sip_needed = corpus * monthly_rate / (((1 + monthly_rate) ** months) - 1)
        else:
            sip_needed = corpus / max(months, 1)
        
        return {
            'current_age': current_age,
            'retirement_age': retirement_age,
            'years_to_retire': years_to_retire,
            'current_monthly_expense': monthly_expense,
            'future_monthly_expense': round(future_expense),
            'required_corpus': round(corpus),
            'monthly_sip_needed': round(sip_needed),
            'annual_investment_needed': round(sip_needed * 12)
        }
    
    def calculate_investment_returns(self, principal, rate, years, investment_type='lumpsum', monthly_sip=0):
        """Calculate returns for different investment types"""
        if investment_type == 'lumpsum':
            # Compound interest
            amount = principal * ((1 + rate/100) ** years)
            returns = amount - principal
            return {
                'invested': principal,
                'returns': round(returns),
                'total_value': round(amount),
                'effective_return': round(returns / principal * 100, 1) if principal > 0 else 0,
                'yearly_breakdown': self._yearly_breakdown(principal, rate, years)
            }
        elif investment_type == 'sip':
            monthly_rate = rate / 100 / 12
            months = years * 12
            if monthly_rate > 0:
                amount = monthly_sip * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
            else:
                amount = monthly_sip * months
            invested = monthly_sip * months
            returns = amount - invested
            return {
                'invested': round(invested),
                'returns': round(returns),
                'total_value': round(amount),
                'monthly_sip': monthly_sip,
                'effective_return': round(returns / invested * 100, 1) if invested > 0 else 0,
                'yearly_breakdown': self._sip_yearly_breakdown(monthly_sip, rate, years)
            }
    
    def _yearly_breakdown(self, principal, rate, years):
        breakdown = []
        for y in range(1, years + 1):
            value = principal * ((1 + rate/100) ** y)
            breakdown.append({'year': y, 'value': round(value), 'gain': round(value - principal)})
        return breakdown
    
    def _sip_yearly_breakdown(self, monthly_sip, rate, years):
        breakdown = []
        monthly_rate = rate / 100 / 12
        for y in range(1, years + 1):
            months = y * 12
            if monthly_rate > 0:
                value = monthly_sip * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
            else:
                value = monthly_sip * months
            invested = monthly_sip * months
            breakdown.append({'year': y, 'value': round(value), 'invested': round(invested), 'gain': round(value - invested)})
        return breakdown
    
    def _calculate_emi(self, principal, annual_rate, years):
        """Calculate EMI amount"""
        if principal <= 0 or years <= 0:
            return 0
        monthly_rate = annual_rate / 100 / 12
        months = years * 12
        if monthly_rate == 0:
            return principal / months
        emi = principal * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
        return round(emi)
    
    def _get_car_segments(self, budget):
        """Get car segments based on budget"""
        segments = []

        if budget >= 500000:
            segments.append({'segment': 'Hatchback', 'range': '₹4-8 Lakh', 'examples': 'Swift, i20, Baleno'})
        if budget >= 800000:
            segments.append({'segment': 'Sedan', 'range': '₹8-15 Lakh', 'examples': 'City, Verna, Ciaz'})
        if budget >= 1200000:
            segments.append({'segment': 'Compact SUV', 'range': '₹10-18 Lakh', 'examples': 'Creta, Seltos, Nexon'})
        if budget >= 1800000:
            segments.append({'segment': 'Mid-Size SUV', 'range': '₹15-30 Lakh', 'examples': 'Scorpio N, XUV700, Harrier'})
        if budget >= 3000000:
            segments.append({'segment': 'Premium SUV', 'range': '₹30-60 Lakh', 'examples': 'Fortuner, Gloster, Meridian'})
        if not segments:
            segments.append({'segment': 'Entry Level', 'range': '₹3-5 Lakh', 'examples': 'Alto, S-Presso, Kwid'})
        return segments

    def get_ai_playbooks(self, monthly_salary, profession='', state='', risk_appetite='moderate'):
        """Return in-app strategy playbooks with no external redirects."""
        revenue_band = 'starter' if monthly_salary < 50000 else 'growth' if monthly_salary < 150000 else 'scale'
        marketing_budget = max(5000, monthly_salary * 0.08)

        if revenue_band == 'starter':
            channel_split = [
                {'channel': 'WhatsApp + Referrals', 'min_pct': 30, 'max_pct': 45},
                {'channel': 'Instagram Reels', 'min_pct': 25, 'max_pct': 35},
                {'channel': 'Local SEO + Google Business', 'min_pct': 20, 'max_pct': 30},
                {'channel': 'Performance Ads', 'min_pct': 10, 'max_pct': 20},
            ]
        elif revenue_band == 'growth':
            channel_split = [
                {'channel': 'Meta Ads (Lead + Retargeting)', 'min_pct': 30, 'max_pct': 40},
                {'channel': 'Google Search Ads', 'min_pct': 20, 'max_pct': 30},
                {'channel': 'Content/SEO', 'min_pct': 20, 'max_pct': 30},
                {'channel': 'Referral Programs', 'min_pct': 10, 'max_pct': 20},
            ]
        else:
            channel_split = [
                {'channel': 'Performance Ads (Multi-channel)', 'min_pct': 35, 'max_pct': 50},
                {'channel': 'Brand + Content Engine', 'min_pct': 20, 'max_pct': 30},
                {'channel': 'Affiliate/Partnership', 'min_pct': 15, 'max_pct': 25},
                {'channel': 'Retention CRM Journeys', 'min_pct': 10, 'max_pct': 20},
            ]

        marketing_strategies = {
            'monthly_budget_range': {
                'min': int(marketing_budget * 0.8),
                'max': int(marketing_budget * 1.2),
            },
            'channel_split': channel_split,
            'kpi_targets': [
                {'metric': 'Lead Conversion Rate', 'target': '8% - 15%'},
                {'metric': 'Customer Acquisition Cost', 'target': 'Below 1.5x average order profit'},
                {'metric': 'Retention (90-day)', 'target': '35% - 50%'},
                {'metric': 'ROAS', 'target': '2.5x - 4x'},
            ],
            'execution_calendar': [
                'Week 1: Define offer + audience + campaign objective',
                'Week 2: Launch 2 ad variants + 1 organic content theme',
                'Week 3: Pause weak creatives, scale best performer by 20%',
                'Week 4: Publish insights and double down on winning channel',
            ],
        }

        business_techniques = [
            {
                'title': 'Margin-First Pricing',
                'action': 'Set floor price by cost + minimum target margin, then test 3-tier pricing.',
                'impact_window': '30-45 days',
            },
            {
                'title': 'Cash-Flow Discipline',
                'action': 'Split inflow: 50% operations, 20% growth, 20% reserve, 10% founder draw.',
                'impact_window': 'Immediate',
            },
            {
                'title': 'Inventory Velocity Control',
                'action': 'Tag SKUs as fast/slow/dead stock and move dead stock with bundle offers.',
                'impact_window': '30-60 days',
            },
            {
                'title': 'Debt-to-Revenue Guardrail',
                'action': 'Keep monthly EMI commitments below 25% of monthly revenue inflow.',
                'impact_window': 'Continuous',
            },
            {
                'title': 'Repeat-Revenue System',
                'action': 'Create subscription or membership-like recurring package for top service.',
                'impact_window': '60-90 days',
            },
        ]

        financial_ideologies = [
            {'name': 'Liquidity First', 'meaning': 'Keep 3-6 months emergency reserves before aggressive expansion.'},
            {'name': 'Risk Layering', 'meaning': 'Mix low-risk, moderate-risk, and growth bets instead of all-in allocation.'},
            {'name': 'Goal-Based Capital', 'meaning': 'Map each rupee to explicit goals: runway, growth, protection, wealth.'},
            {'name': 'Tax-Aware Strategy', 'meaning': 'Prioritize post-tax returns, not just headline return percentages.'},
            {'name': 'Data Over Emotion', 'meaning': 'Review weekly KPIs and act on numbers, not market noise.'},
        ]

        opportunity_catalog = {
            'govt_schemes': [
                {'name': 'PMMY (Mudra)', 'for': 'Micro/small business loans', 'benefit': 'Collateral-free up to applicable limits'},
                {'name': 'Stand-Up India', 'for': 'Women/SC/ST entrepreneurs', 'benefit': 'Bank-supported startup funding'},
                {'name': 'Atal Pension Yojana', 'for': 'Long-term pension planning', 'benefit': 'Defined pension after 60'},
            ],
            'bonds_and_savings': [
                {'name': 'Government Bonds', 'risk': 'Low', 'range': '6.5% - 7.5%'},
                {'name': 'Sovereign Gold Bond', 'risk': 'Low', 'range': 'Gold appreciation + 2.5%'},
                {'name': 'NSC / KVP / PPF', 'risk': 'Low', 'range': '7.1% - 7.7%'},
            ],
            'post_office_products': [
                {'name': 'PPF', 'tenure': '15 years', 'tax': 'EEE'},
                {'name': 'SCSS', 'tenure': '5 years', 'tax': '80C + taxable interest'},
                {'name': 'MIS', 'tenure': '5 years', 'tax': 'Interest taxable'},
            ],
            'business_playbooks': [
                {'name': 'Local Services Growth', 'focus': 'Referrals + Google Business + WhatsApp retention'},
                {'name': 'E-commerce Growth', 'focus': 'AOV bundles + retargeting + email automation'},
                {'name': 'Consulting Growth', 'focus': 'Offer ladder + authority content + case studies'},
            ],
        }

        return {
            'profile': {
                'monthly_salary': monthly_salary,
                'profession': profession or 'General',
                'state': state or 'India',
                'risk_appetite': risk_appetite,
                'revenue_band': revenue_band,
            },
            'marketing_strategies': marketing_strategies,
            'business_techniques': business_techniques,
            'financial_ideologies': financial_ideologies,
            'opportunity_catalog': opportunity_catalog,
        }

    def get_future_readiness_2040(self, monthly_salary, age, risk_appetite='moderate'):
        """Return a long-horizon (2040+) financial readiness plan."""
        monthly_salary = max(float(monthly_salary or 0), 0)
        age = max(int(age or 30), 18)
        years_to_2040 = max(0, 2040 - datetime.now().year)

        base_investable = monthly_salary * 0.25
        emergency_fund_target = monthly_salary * 6
        inflation_assumption = 0.06

        if risk_appetite == 'high':
            allocation = {'growth_equity': 60, 'stable_debt': 20, 'alternatives': 20}
            expected_return = 0.115
        elif risk_appetite == 'low':
            allocation = {'growth_equity': 35, 'stable_debt': 45, 'alternatives': 20}
            expected_return = 0.085
        else:
            allocation = {'growth_equity': 50, 'stable_debt': 30, 'alternatives': 20}
            expected_return = 0.10

        years = max(years_to_2040, 1)
        real_return = ((1 + expected_return) / (1 + inflation_assumption)) - 1

        monthly_rate = expected_return / 12
        total_months = years * 12
        if monthly_rate > 0:
            future_value = base_investable * (((1 + monthly_rate) ** total_months - 1) / monthly_rate) * (1 + monthly_rate)
        else:
            future_value = base_investable * total_months

        inflation_multiplier = (1 + inflation_assumption) ** years
        inflation_adjusted_corpus = future_value / max(inflation_multiplier, 1)

        milestones = [
            {
                'year': datetime.now().year + 1,
                'goal': 'Stability Layer',
                'action': 'Build 6-month emergency fund and clear high-interest debt first.',
            },
            {
                'year': datetime.now().year + 3,
                'goal': 'Automation Layer',
                'action': 'Automate SIP, EPF/NPS, and yearly step-up by 10-12%.',
            },
            {
                'year': datetime.now().year + 7,
                'goal': 'Opportunity Layer',
                'action': 'Allocate part of gains to future themes: AI infra, climate-tech, and healthcare innovation funds.',
            },
            {
                'year': 2040,
                'goal': 'Freedom Layer',
                'action': 'Target FI runway: annual passive income >= 70% of projected lifestyle cost.',
            },
        ]

        future_risks = [
            'AI disruption risk: keep re-skilling budget each year',
            'Healthcare inflation: maintain health cover and top-up plan',
            'Climate/energy shocks: diversify geography and sectors',
            'Currency/global risk: allocate a small international sleeve',
        ]

        return {
            'profile': {
                'monthly_salary': monthly_salary,
                'age': age,
                'risk_appetite': risk_appetite,
                'years_to_2040': years_to_2040,
            },
            'plan': {
                'monthly_investment_target': round(base_investable),
                'emergency_fund_target': round(emergency_fund_target),
                'expected_return_pct': round(expected_return * 100, 1),
                'real_return_pct': round(real_return * 100, 1),
                'allocation': allocation,
                'projected_corpus_2040': round(future_value),
                'inflation_adjusted_corpus_2040': round(inflation_adjusted_corpus),
            },
            'milestones': milestones,
            'future_risks': future_risks,
        }
    
    def get_tax_saving_suggestions(self, annual_salary):
        """Tax saving investment suggestions"""
        suggestions = []
        
        # Section 80C - Up to 1.5 Lakh
        suggestions.append({
            'section': '80C',
            'limit': 150000,
            'options': [
                {'name': 'PPF', 'max': 150000, 'lock_in': '15 years', 'return': '7.1%'},
                {'name': 'ELSS Mutual Fund', 'max': 150000, 'lock_in': '3 years', 'return': '10-15%'},
                {'name': 'Tax Saving FD', 'max': 150000, 'lock_in': '5 years', 'return': '6.5-7%'},
                {'name': 'NPS (Tier 1)', 'max': 150000, 'lock_in': 'Till 60', 'return': '9-12%'},
                {'name': 'Life Insurance Premium', 'max': 150000, 'lock_in': 'Policy term', 'return': '4-6%'},
                {'name': 'NSC', 'max': 150000, 'lock_in': '5 years', 'return': '7.7%'},
            ]
        })
        
        # Section 80CCD(1B) - Additional 50K for NPS
        suggestions.append({
            'section': '80CCD(1B)',
            'limit': 50000,
            'options': [
                {'name': 'NPS Additional', 'max': 50000, 'lock_in': 'Till 60', 'return': '9-12%'}
            ]
        })
        
        # Section 80D - Health Insurance
        suggestions.append({
            'section': '80D',
            'limit': 75000,
            'options': [
                {'name': 'Health Insurance (Self+Family)', 'max': 25000, 'lock_in': 'Annual', 'return': 'Protection'},
                {'name': 'Health Insurance (Parents)', 'max': 50000, 'lock_in': 'Annual', 'return': 'Protection'},
            ]
        })
        
        total_deduction = 150000 + 50000 + 75000  # 2.75 Lakh
        tax_saved = total_deduction * 0.30 if annual_salary > 1500000 else total_deduction * 0.20
        
        return {
            'suggestions': suggestions,
            'total_deduction_available': total_deduction,
            'estimated_tax_saved': round(tax_saved),
            'annual_salary': annual_salary
        }

    def analyze_loan(self, loan_type, principal, interest_rate, tenure_months, emi_amount, paid_months, monthly_salary):
        """AI analysis: is this loan good or bad?"""
        total_interest = (emi_amount * tenure_months) - principal
        interest_pct = (total_interest / principal) * 100 if principal > 0 else 0
        remaining_months = tenure_months - paid_months
        remaining_balance = emi_amount * remaining_months
        total_cost = emi_amount * tenure_months
        emi_to_income = (emi_amount / monthly_salary * 100) if monthly_salary > 0 else 100

        # Rating system
        score = 100
        reasons = []
        tips = []

        # Interest rate benchmarks by loan type
        benchmarks = {
            'Home': 9.0, 'Car': 9.5, 'Two Wheeler': 12.0, 'Education': 9.0,
            'Personal': 14.0, 'Gold': 10.0, 'Credit Card': 24.0, 'Business': 14.0
        }
        benchmark = benchmarks.get(loan_type, 12.0)

        if interest_rate > benchmark + 3:
            score -= 30
            reasons.append(f'Interest rate ({interest_rate}%) is much higher than benchmark ({benchmark}%)')
            tips.append(f'Consider refinancing to a lower rate. Current benchmark for {loan_type} loans is ~{benchmark}%')
        elif interest_rate > benchmark:
            score -= 15
            reasons.append(f'Interest rate ({interest_rate}%) is above average for {loan_type} loans')
            tips.append('Shop around for better rates or negotiate with your lender')

        if emi_to_income > 50:
            score -= 30
            reasons.append(f'EMI takes {emi_to_income:.0f}% of income — very high debt burden')
            tips.append('Try to increase income or prepay to reduce burden')
        elif emi_to_income > 30:
            score -= 15
            reasons.append(f'EMI takes {emi_to_income:.0f}% of income — moderate debt burden')
        else:
            reasons.append(f'EMI is {emi_to_income:.0f}% of income — manageable')

        if interest_pct > 100:
            score -= 20
            reasons.append(f'Total interest ({interest_pct:.0f}% of principal) is very high')
            tips.append('Consider prepaying or part-paying to reduce interest')
        elif interest_pct > 50:
            score -= 10
            reasons.append(f'Total interest is {interest_pct:.0f}% of principal')

        # Asset-building loans are generally better
        if loan_type in ['Home', 'Education', 'Gold', 'Business']:
            score += 10
            reasons.append(f'{loan_type} loan builds an appreciating asset — generally a good loan')
        elif loan_type == 'Credit Card':
            score -= 20
            reasons.append('Credit card debt has very high interest — pay off immediately')
            tips.append('Transfer balance to a lower-rate personal loan if payoff isn\'t possible')

        score = max(0, min(100, score))

        if score >= 75:
            verdict = 'Good'
            badge_color = 'success'
        elif score >= 50:
            verdict = 'Average'
            badge_color = 'warning'
        else:
            verdict = 'Bad'
            badge_color = 'danger'

        # Prepayment suggestion
        if remaining_months > 12 and interest_rate > 8:
            monthly_extra = emi_amount * 0.1
            saved_interest = monthly_extra * remaining_months * (interest_rate / 100 / 12)
            tips.append(f'Paying just ₹{monthly_extra:,.0f} extra/month could save ~₹{saved_interest:,.0f} in interest')

        return {
            'verdict': verdict,
            'score': score,
            'badge_color': badge_color,
            'total_interest': round(total_interest),
            'interest_pct': round(interest_pct, 1),
            'emi_to_income': round(emi_to_income, 1),
            'remaining_balance': round(remaining_balance),
            'total_cost': round(total_cost),
            'reasons': reasons,
            'tips': tips
        }

    def get_credit_card_offers(self, monthly_salary, total_debts):
        """Suggest credit card offers based on income and profile."""
        offers = []
        if monthly_salary >= 25000:
            offers.append({
                'card': 'SBI SimplyCLICK',
                'benefit': '10X rewards on online shopping',
                'annual_fee': '₹499 (waived on ₹1L spend)',
                'apply_url': 'https://www.sbicard.com/en/personal/credit-cards/shopping/simplyclick-sbi-card.page',
                'best_for': 'Online Shopping'
            })
        if monthly_salary >= 50000:
            offers.append({
                'card': 'HDFC Regalia',
                'benefit': '4 reward points per ₹150 + lounge access',
                'annual_fee': '₹2,500',
                'apply_url': 'https://www.hdfcbank.com/personal/pay/cards/credit-cards/regalia-credit-card',
                'best_for': 'Travel & Rewards'
            })
            offers.append({
                'card': 'Axis Flipkart',
                'benefit': '5% cashback on Flipkart, 4% on preferred partners',
                'annual_fee': '₹500',
                'apply_url': 'https://www.axisbank.com/retail/cards/credit-card/flipkart-axis-bank-credit-card',
                'best_for': 'Flipkart Shopping'
            })
        if monthly_salary >= 100000:
            offers.append({
                'card': 'HDFC Infinia',
                'benefit': '5 reward points per ₹150 + unlimited lounge',
                'annual_fee': '₹12,500',
                'apply_url': 'https://www.hdfcbank.com/personal/pay/cards/credit-cards/infinia-credit-card',
                'best_for': 'Premium Travel'
            })
            offers.append({
                'card': 'Amex Platinum',
                'benefit': 'Premium travel benefits + Taj/Marriott perks',
                'annual_fee': '₹60,000',
                'apply_url': 'https://www.americanexpress.com/in/credit-cards/platinum-card/',
                'best_for': 'Ultra Premium Lifestyle'
            })

        # Balance transfer suggestion if high debt
        if total_debts > monthly_salary * 3:
            offers.append({
                'card': 'Balance Transfer',
                'benefit': f'Transfer ₹{total_debts:,.0f} debt to 0% EMI for 6-12 months',
                'annual_fee': 'Processing fee 1-2%',
                'apply_url': 'https://www.bankbazaar.com/credit-card/balance-transfer.html',
                'best_for': 'Debt Management'
            })

        return offers

    def get_gold_silver_analysis(self):
        """AI analysis for gold and silver prices with 18K/22K/24K karat data and day/month/year history."""
        today = datetime.now()
        day_of_year = today.timetuple().tm_yday

        # Base prices from rate_monitor
        karats = {
            '24K': {'base': COMMODITY_BASE['gold_24k_per_gram'], 'fluct': COMMODITY_BASE['gold_24k_fluctuation']},
            '22K': {'base': COMMODITY_BASE['gold_22k_per_gram'], 'fluct': COMMODITY_BASE['gold_22k_fluctuation']},
            '18K': {'base': COMMODITY_BASE['gold_18k_per_gram'], 'fluct': COMMODITY_BASE['gold_18k_fluctuation']},
        }
        silver_base = COMMODITY_BASE['silver_per_gram']
        silver_fluct = COMMODITY_BASE['silver_fluctuation']

        def _gold_price(base, fluct, doy, noise=0):
            # Sine-based smooth fluctuation for realistic price movement
            import math
            return base + math.sin(doy * 0.17) * fluct * 0.6 + math.cos(doy * 0.31) * fluct * 0.4 + noise

        def _silver_price(base, fluct, doy, noise=0):
            import math
            return base + math.sin(doy * 0.21) * fluct * 0.5 + math.cos(doy * 0.37) * fluct * 0.5 + noise

        # Current prices
        gold_prices = {}
        for k, v in karats.items():
            gold_prices[k] = round(_gold_price(v['base'], v['fluct'], day_of_year), 2)

        silver_price = round(_silver_price(silver_base, silver_fluct, day_of_year), 2)

        # --- Generate histories for 3 time ranges ---
        def _gen_gold_history(days, label_fmt, base, fluct, noise_scale=1):
            hist = []
            for i in range(days, -1, -1):
                d = today - timedelta(days=i)
                doy = d.timetuple().tm_yday
                noise = ((i % 5) * 6 - 12) * noise_scale
                p = _gold_price(base, fluct, doy, noise)
                hist.append({'date': d.strftime(label_fmt), 'price': round(p, 2)})
            return hist

        def _gen_silver_history(days, label_fmt, noise_scale=1):
            hist = []
            for i in range(days, -1, -1):
                d = today - timedelta(days=i)
                doy = d.timetuple().tm_yday
                noise = ((i % 4) * 0.6 - 0.9) * noise_scale
                p = _silver_price(silver_base, silver_fluct, doy, noise)
                hist.append({'date': d.strftime(label_fmt), 'price': round(p, 2)})
            return hist

        # Gold histories per karat
        gold_data = {}
        for k, v in karats.items():
            day_hist = _gen_gold_history(30, '%d %b', v['base'], v['fluct'])
            month_hist = _gen_gold_history(365, '%b %Y', v['base'], v['fluct'], noise_scale=2)
            # Sample monthly: take one point per ~30 days
            month_sampled = [month_hist[i] for i in range(0, len(month_hist), 30)] + [month_hist[-1]]
            year_hist = []
            for yr_offset in range(4, -1, -1):
                d = today - timedelta(days=yr_offset * 365)
                doy = d.timetuple().tm_yday
                # Simulate yearly growth: gold appreciates ~10% per year
                growth = (1 - yr_offset * 0.10)
                p = v['base'] * growth + (doy % 40) * (v['fluct'] / 20) - v['fluct']
                year_hist.append({'date': d.strftime('%Y'), 'price': round(p, 2)})

            week_ago = day_hist[-8]['price'] if len(day_hist) >= 8 else gold_prices[k]
            change = gold_prices[k] - week_ago
            change_pct = (change / week_ago) * 100 if week_ago else 0
            avg_30 = sum(h['price'] for h in day_hist) / len(day_hist)
            trend = 'Bullish' if gold_prices[k] > avg_30 else 'Bearish'

            gold_data[k] = {
                'current_price': gold_prices[k],
                'price_10g': round(gold_prices[k] * 10, 2),
                'change': round(change, 2),
                'change_pct': round(change_pct, 2),
                'trend': trend,
                'history_day': day_hist,
                'history_month': month_sampled,
                'history_year': year_hist,
            }

        # Silver histories
        silver_day = _gen_silver_history(30, '%d %b')
        silver_month_full = _gen_silver_history(365, '%b %Y', noise_scale=2)
        silver_month = [silver_month_full[i] for i in range(0, len(silver_month_full), 30)] + [silver_month_full[-1]]
        silver_year = []
        for yr_offset in range(4, -1, -1):
            d = today - timedelta(days=yr_offset * 365)
            doy = d.timetuple().tm_yday
            growth = (1 - yr_offset * 0.08)
            p = silver_base * growth + (doy % 30) * (silver_fluct / 15) - silver_fluct
            silver_year.append({'date': d.strftime('%Y'), 'price': round(p, 2)})

        silver_week_ago = silver_day[-8]['price'] if len(silver_day) >= 8 else silver_price
        silver_change = silver_price - silver_week_ago
        silver_change_pct = (silver_change / silver_week_ago) * 100 if silver_week_ago else 0
        silver_avg_30 = sum(h['price'] for h in silver_day) / len(silver_day)
        silver_trend = 'Bullish' if silver_price > silver_avg_30 else 'Bearish'

        # AI tips
        gold_tips = []
        gold_trend_24k = gold_data['24K']['trend']
        if gold_trend_24k == 'Bullish':
            gold_tips.append('Gold prices trending up — good if already invested, wait for dip to buy more')
            gold_tips.append('Consider Sovereign Gold Bonds for 2.5% extra annual returns')
        else:
            gold_tips.append('Gold prices trending down — good buying opportunity')
            gold_tips.append('Consider SIP-style gold investment via Gold ETF/SGB')
        gold_tips.append('22K gold is best for jewelry, 24K for investment (coins/bars/ETFs)')

        silver_tips = []
        if silver_trend == 'Bullish':
            silver_tips.append('Silver showing upward trend — industrial demand driving prices')
            silver_tips.append('Silver ETFs offer easier exposure than physical silver')
        else:
            silver_tips.append('Silver dipping — accumulate for long-term as industrial metal')
            silver_tips.append('Physical silver coins from banks offer best purity')

        return {
            'gold': gold_data,
            'gold_tips': gold_tips,
            'silver': {
                'current_price': silver_price,
                'unit': 'per gram',
                'price_kg': round(silver_price * 1000, 2),
                'change': round(silver_change, 2),
                'change_pct': round(silver_change_pct, 2),
                'trend': silver_trend,
                'history_day': silver_day,
                'history_month': silver_month,
                'history_year': silver_year,
                'tips': silver_tips,
            },
            'last_updated': today.strftime('%d %b %Y, %I:%M %p'),
        }

    def get_buy_timing_suggestion(self, goal_category, target_amount):
        """AI suggestion for best time to buy car/bike based on seasonal patterns."""
        today = datetime.now()
        month = today.month
        suggestions = []

        if goal_category and goal_category.lower() in ['car', 'automobile', 'vehicle']:
            # Best months for car buying
            best_months = {
                3: ('March — Financial year-end clearance sales', 95),
                9: ('September — Navratri/festive season deals', 90),
                10: ('October — Dussehra/Diwali offers', 90),
                11: ('November — Year-end model clearance begins', 85),
                12: ('December — Year-end clearance with max discounts', 92),
            }
            current_score = best_months.get(month, (None, 50))

            if current_score[1] >= 85:
                suggestions.append({
                    'verdict': 'Great Time to Buy!',
                    'badge': 'success',
                    'reason': current_score[0],
                    'tip': f'Negotiate hard — dealers want to clear stock. Expected savings: ₹{target_amount * 0.05:,.0f} to ₹{target_amount * 0.12:,.0f}'
                })
            elif current_score[1] >= 60:
                suggestions.append({
                    'verdict': 'Decent Time',
                    'badge': 'warning',
                    'reason': 'No major sale season right now',
                    'tip': 'You can buy but waiting for year-end or festival season could save 5-12%'
                })
            else:
                next_best = min((m for m in best_months if m > month), default=3)
                suggestions.append({
                    'verdict': 'Wait if Possible',
                    'badge': 'danger',
                    'reason': 'No active sale season',
                    'tip': f'Best to wait for {best_months[next_best][0]}. Expected savings: 5-12% off showroom price'
                })

            suggestions.append({
                'category': 'Car/Vehicle',
                'general_tips': [
                    'Always compare on-road price across 3+ dealers',
                    'Check for corporate/government employee discounts',
                    'Consider pre-approved car loans for lower interest rates (7-9%)',
                    'BS-VI diesel resale value is declining — consider petrol/CNG/EV',
                    'Extended warranty is usually worth it for 2 more years',
                    f'For ₹{target_amount:,.0f} budget, save at least 20% (₹{target_amount * 0.2:,.0f}) as down payment'
                ]
            })

        elif goal_category and goal_category.lower() in ['bike', 'two wheeler', 'scooter', 'motorcycle']:
            best_months = {
                3: ('March — Year-end offers', 88),
                9: ('September — Navratri exchange offers', 85),
                10: ('October — Festive discounts', 90),
                11: ('November — Special festive offers', 85),
            }
            current_score = best_months.get(month, (None, 50))

            if current_score[1] and current_score[1] >= 85:
                suggestions.append({
                    'verdict': 'Good Time to Buy!',
                    'badge': 'success',
                    'reason': current_score[0],
                    'tip': f'Negotiate for accessories + insurance deals. Savings: ₹{target_amount * 0.03:,.0f} to ₹{target_amount * 0.08:,.0f}'
                })
            else:
                suggestions.append({
                    'verdict': 'Wait for Festival Season',
                    'badge': 'warning',
                    'reason': 'No major two-wheeler sale right now',
                    'tip': 'Festival season (Sept-Nov) offers best exchange bonuses and free accessories'
                })

            suggestions.append({
                'category': 'Bike/Two Wheeler',
                'general_tips': [
                    'Exchange old vehicle for ₹3,000-15,000 bonus',
                    'Compare EMI plans — 0% EMI is usually better than cash discount',
                    'Consider EV scooters — lower running cost & govt subsidies available',
                    'Check state EV subsidy (up to ₹30,000 in some states)',
                    f'For ₹{target_amount:,.0f} budget, avoid loans — save and buy outright'
                ]
            })

        return suggestions

    def get_grocery_offers(self, monthly_salary=0):
        import random
        from datetime import datetime, timedelta

        today = datetime.now()
        stores = [
            {
                'name': 'BigBasket',
                'icon': 'shopping_basket',
                'color': '#84C225',
                'offers': [
                    {'title': 'Fresh Fruits & Veggies', 'discount': 'Up to 40% OFF', 'code': 'FRESH40', 'min_order': 500, 'valid_till': (today + timedelta(days=3)).strftime('%d %b'), 'category': 'Fruits & Vegetables'},
                    {'title': 'Monthly Grocery Pack', 'discount': 'Flat ₹200 OFF on ₹1500+', 'code': 'BBMONTH', 'min_order': 1500, 'valid_till': (today + timedelta(days=7)).strftime('%d %b'), 'category': 'Staples & Atta'},
                    {'title': 'Dairy & Breakfast', 'discount': 'Buy 2 Get 1 Free', 'code': None, 'min_order': 300, 'valid_till': (today + timedelta(days=5)).strftime('%d %b'), 'category': 'Dairy'},
                ]
            },
            {
                'name': 'Blinkit',
                'icon': 'bolt',
                'color': '#F8D210',
                'offers': [
                    {'title': '10-Min Delivery Special', 'discount': 'Flat ₹100 OFF', 'code': 'BLINK100', 'min_order': 499, 'valid_till': (today + timedelta(days=2)).strftime('%d %b'), 'category': 'All Categories'},
                    {'title': 'Snacks & Beverages Fest', 'discount': 'Up to 50% OFF', 'code': 'SNACK50', 'min_order': 200, 'valid_till': (today + timedelta(days=4)).strftime('%d %b'), 'category': 'Snacks & Drinks'},
                    {'title': 'Household Essentials', 'discount': 'Flat 30% OFF on ₹800+', 'code': 'HOME30', 'min_order': 800, 'valid_till': (today + timedelta(days=6)).strftime('%d %b'), 'category': 'Cleaning & Household'},
                ]
            },
            {
                'name': 'Zepto',
                'icon': 'flash_on',
                'color': '#7B2D8E',
                'offers': [
                    {'title': 'New User Offer', 'discount': 'Flat ₹150 OFF + Free Delivery', 'code': 'ZEPTONEW', 'min_order': 299, 'valid_till': (today + timedelta(days=10)).strftime('%d %b'), 'category': 'First Order'},
                    {'title': 'Weekend Grocery Sale', 'discount': 'Up to 60% OFF on Staples', 'code': 'WKND60', 'min_order': 500, 'valid_till': (today + timedelta(days=3)).strftime('%d %b'), 'category': 'Rice, Dal & Oil'},
                    {'title': 'Fresh Meat & Fish', 'discount': '25% OFF', 'code': 'FRESH25', 'min_order': 400, 'valid_till': (today + timedelta(days=2)).strftime('%d %b'), 'category': 'Non-Veg'},
                ]
            },
            {
                'name': 'Swiggy Instamart',
                'icon': 'delivery_dining',
                'color': '#FC8019',
                'offers': [
                    {'title': 'Instamart Saver', 'discount': 'Free Delivery on ₹199+', 'code': None, 'min_order': 199, 'valid_till': (today + timedelta(days=5)).strftime('%d %b'), 'category': 'All Categories'},
                    {'title': 'Baby & Personal Care', 'discount': 'Flat 35% OFF', 'code': 'CARE35', 'min_order': 600, 'valid_till': (today + timedelta(days=4)).strftime('%d %b'), 'category': 'Personal Care'},
                    {'title': 'Cooking Essentials Pack', 'discount': 'Up to 45% OFF', 'code': 'COOK45', 'min_order': 700, 'valid_till': (today + timedelta(days=6)).strftime('%d %b'), 'category': 'Masala, Oil & More'},
                ]
            },
            {
                'name': 'JioMart',
                'icon': 'storefront',
                'color': '#0078D4',
                'offers': [
                    {'title': 'Smart Saver Combo', 'discount': 'Extra 10% OFF on Combos', 'code': 'JIOSMART', 'min_order': 500, 'valid_till': (today + timedelta(days=7)).strftime('%d %b'), 'category': 'Combo Offers'},
                    {'title': 'Atta, Rice & Dal Sale', 'discount': 'Up to ₹300 OFF', 'code': 'STAPLE300', 'min_order': 1000, 'valid_till': (today + timedelta(days=5)).strftime('%d %b'), 'category': 'Staples'},
                ]
            },
        ]

        # Shuffle offers for variety each time
        for store in stores:
            random.shuffle(store['offers'])

        # Add a smart tip based on salary
        smart_tip = 'Compare prices across platforms before ordering — prices differ by 10-30% for the same product.'
        if monthly_salary and monthly_salary > 0:
            grocery_budget = monthly_salary * 0.15
            smart_tip = f'Recommended grocery budget: ₹{grocery_budget:,.0f}/month (15% of salary). {smart_tip}'

        return {
            'stores': stores,
            'smart_tip': smart_tip,
            'last_updated': today.strftime('%d %b %Y, %I:%M %p')
        }

    def get_business_ideas(self, profession='', monthly_salary=0, age=30, risk_appetite='moderate', state='', total_savings=0, total_investments=0):
        """AI-powered business idea recommender based on user profile, wealth & government schemes."""

        investable_capital = total_savings + total_investments
        annual_income = monthly_salary * 12

        # ---- Determine investment tier ----
        if investable_capital >= 2500000 or monthly_salary >= 150000:
            tier = 'high'
        elif investable_capital >= 500000 or monthly_salary >= 50000:
            tier = 'medium'
        else:
            tier = 'low'

        # ---- State-specific MSME portals ----
        state_portals = {
            'Tamil Nadu': {'portal': 'msme.tn.gov.in', 'scheme': 'NEEDS Scheme — 25% capital subsidy up to ₹25L', 'extra': 'TANSIDCO industrial plots, TIIC loan at 7%'},
            'Karnataka': {'portal': 'karnatakaindustry.gov.in', 'scheme': 'Elevate Program — ₹50L equity for startups', 'extra': 'KIADB industrial plots, Startup Karnataka policy'},
            'Maharashtra': {'portal': 'maitri.mahaonline.gov.in', 'scheme': 'CMEGP — 25-35% subsidy on projects up to ₹50L', 'extra': 'MIDC plots, Marathwada/Vidarbha special package'},
            'Kerala': {'portal': 'ksidc.org', 'scheme': 'Kerala Startup Mission — seed fund up to ₹25L', 'extra': 'KINFRA industrial parks, KSFE chitty loans'},
            'Andhra Pradesh': {'portal': 'apindustries.gov.in', 'scheme': 'YSR Industrial Development — 35% capital subsidy', 'extra': 'APIIC industrial parks, TIDE 2.0'},
            'Telangana': {'portal': 'tsiic.telangana.gov.in', 'scheme': 'T-Hub — mentoring & co-working for startups', 'extra': 'WE Hub for women, T-IDEA scheme ₹15L'},
            'Gujarat': {'portal': 'ic.gujarat.gov.in', 'scheme': 'Interest subsidy 7-9% for 5 years', 'extra': 'GIDC plots, Vibrant Gujarat MSME support'},
            'Uttar Pradesh': {'portal': 'udyogbandhu.com', 'scheme': 'ODOP — One District One Product subsidy', 'extra': 'UP MSME Sathi portal, CM Yuva Udyami Yojana'},
            'Rajasthan': {'portal': 'rajudyogmitra.rajasthan.gov.in', 'scheme': 'RIPS — 30% capital subsidy for manufacturing', 'extra': 'RIICO industrial plots, tech upgrade subsidy'},
            'Madhya Pradesh': {'portal': 'mpmsme.gov.in', 'scheme': 'Mukhyamantri Yuva Udyami Yojana — 15% margin money', 'extra': 'AKVN industrial areas, interest subsidy'},
            'West Bengal': {'portal': 'banglashilpa.wb.gov.in', 'scheme': 'Bangla Shilpa Portal — single window clearance', 'extra': 'WBIDC industrial parks, MSME credit linked subsidy'},
            'Punjab': {'portal': 'pbindustries.gov.in', 'scheme': 'Ghar Ghar Nigam — employment-linked subsidy', 'extra': 'PSIEC industrial plots, PIDB support'},
            'Haryana': {'portal': 'haryanaindustries.gov.in', 'scheme': 'Enterprise Promotion Policy — 50% subsidy on DG sets', 'extra': 'HSIIDC industrial plots, Faridabad MSME cluster'},
            'Bihar': {'portal': 'industries.bihar.gov.in', 'scheme': 'Bihar Industrial Incentive Policy — 30% capital subsidy', 'extra': 'BIADA industrial areas, Udyami Yojana ₹10L'},
            'Odisha': {'portal': 'investodisha.gov.in', 'scheme': 'Invest Odisha — IPR capital subsidy up to 30%', 'extra': 'IDCO industrial areas, startup policy'},
            'Delhi': {'portal': 'doitc.delhi.gov.in', 'scheme': 'Delhi Startup Policy — ₹10L seed fund', 'extra': 'DSIIDC industrial areas, DFC co-working spaces'},
        }

        state_info = state_portals.get(state, {
            'portal': 'msme.gov.in',
            'scheme': 'PMEGP — 15-35% subsidy on projects up to ₹50L',
            'extra': 'Register on Udyam portal for MSME benefits'
        })

        # ---- Central govt schemes applicable to all ----
        central_schemes = [
            {'name': 'PMEGP (PM Employment Generation)', 'subsidy': '15-35% of project cost', 'max_project': '₹50L (manufacturing) / ₹20L (service)', 'portal': 'kviconline.gov.in/pmegp', 'who': 'Anyone 18+, 8th pass for >₹10L projects'},
            {'name': 'Mudra Yojana', 'subsidy': 'Collateral-free loan', 'max_project': 'Shishu ₹50K / Kishore ₹5L / Tarun ₹10L', 'portal': 'mudra.org.in', 'who': 'Any non-farm small business'},
            {'name': 'Stand-Up India', 'subsidy': 'Loan ₹10L to ₹1Cr', 'max_project': '₹1 Crore', 'portal': 'standupmitra.in', 'who': 'SC/ST/Women entrepreneurs'},
            {'name': 'Startup India Seed Fund', 'subsidy': 'Up to ₹50L grant', 'max_project': '₹50L', 'portal': 'startupindia.gov.in', 'who': 'DPIIT recognized startups <2 yrs old'},
            {'name': 'Credit Guarantee (CGTMSE)', 'subsidy': 'Collateral-free loan up to ₹5Cr', 'max_project': '₹5 Crore', 'portal': 'cgtmse.in', 'who': 'MSMEs — manufacturing & service'},
            {'name': 'Udyam Registration', 'subsidy': 'Free MSME benefits — lower interest, govt tenders', 'max_project': 'Applicable to all', 'portal': 'udyamregistration.gov.in', 'who': 'Any business — free registration'},
        ]

        # ---- Profession-based business ideas ----
        all_ideas = {
            'IT/Software': [
                {'name': 'SaaS Product Company', 'investment': '₹2-10L', 'monthly_potential': '₹50K-5L', 'risk': 'moderate', 'icon': 'code', 'color': '#6C5CE7', 'tier': 'medium',
                 'description': 'Build a niche SaaS product (billing, HR, CRM for Indian SMBs). Low infra cost with cloud.', 'govt_scheme': 'Startup India — tax exemption for 3 years + ₹50L seed fund', 'skills_needed': 'Full-stack development, cloud deployment', 'time_to_profit': '6-12 months'},
                {'name': 'IT Training Institute', 'investment': '₹5-15L', 'monthly_potential': '₹1-5L', 'risk': 'low', 'icon': 'school', 'color': '#00B894', 'tier': 'medium',
                 'description': 'Coding bootcamp / IT training center for students. Online + offline hybrid model.', 'govt_scheme': 'Skill India / NSDC affiliation — govt pays per trainee', 'skills_needed': 'Teaching, curriculum design', 'time_to_profit': '3-6 months'},
                {'name': 'Freelance IT Agency', 'investment': '₹50K-2L', 'monthly_potential': '₹30K-3L', 'risk': 'low', 'icon': 'laptop', 'color': '#0984E3', 'tier': 'low',
                 'description': 'Web/app development agency on Upwork, Fiverr, Toptal. No office needed.', 'govt_scheme': 'SEIS (Service Export) — 5% incentive on export earnings', 'skills_needed': 'Web/app development, client management', 'time_to_profit': '1-3 months'},
                {'name': 'Cybersecurity Consulting', 'investment': '₹1-5L', 'monthly_potential': '₹1-8L', 'risk': 'moderate', 'icon': 'security', 'color': '#E17055', 'tier': 'medium',
                 'description': 'Security audit, penetration testing, compliance consulting for MSMEs.', 'govt_scheme': 'MeitY — cybersecurity startup incentives', 'skills_needed': 'Ethical hacking, compliance (ISO 27001)', 'time_to_profit': '3-6 months'},
            ],
            'Doctor/Healthcare': [
                {'name': 'Telemedicine Platform', 'investment': '₹5-20L', 'monthly_potential': '₹2-10L', 'risk': 'moderate', 'icon': 'video_call', 'color': '#6C5CE7', 'tier': 'medium',
                 'description': 'Online doctor consultation platform. Huge demand post-COVID in tier-2/3 cities.', 'govt_scheme': 'Ayushman Bharat Digital Mission — free health ID integration', 'skills_needed': 'Medical license, basic tech', 'time_to_profit': '6-12 months'},
                {'name': 'Diagnostic Lab', 'investment': '₹10-50L', 'monthly_potential': '₹3-15L', 'risk': 'moderate', 'icon': 'biotech', 'color': '#00B894', 'tier': 'high',
                 'description': 'Pathology lab with home sample collection. Franchise models available (Thyrocare, SRL).', 'govt_scheme': 'PMEGP subsidy + State health dept tie-up', 'skills_needed': 'Lab technology, quality management', 'time_to_profit': '6-12 months'},
                {'name': 'Pharmacy / Medical Store', 'investment': '₹5-15L', 'monthly_potential': '₹1-5L', 'risk': 'low', 'icon': 'local_pharmacy', 'color': '#E17055', 'tier': 'medium',
                 'description': 'Generic medicine store or franchise (Apollo, MedPlus). 15-30% margin on medicines.', 'govt_scheme': 'PM Jan Aushadhi Kendra — free franchise, govt supplies', 'skills_needed': 'D.Pharm or pharmacist hire', 'time_to_profit': '3-6 months'},
            ],
            'Teacher/Education': [
                {'name': 'Online Coaching Platform', 'investment': '₹1-5L', 'monthly_potential': '₹50K-5L', 'risk': 'low', 'icon': 'cast_for_education', 'color': '#6C5CE7', 'tier': 'low',
                 'description': 'YouTube channel + paid courses on Udemy/own platform. Record once, earn repeatedly.', 'govt_scheme': 'DIKSHA platform — govt content partnership', 'skills_needed': 'Subject expertise, video recording', 'time_to_profit': '3-6 months'},
                {'name': 'Coaching Center / Tuition', 'investment': '₹2-10L', 'monthly_potential': '₹1-5L', 'risk': 'low', 'icon': 'menu_book', 'color': '#00B894', 'tier': 'low',
                 'description': 'After-school coaching for 10th/12th/competitive exams. High demand in every city.', 'govt_scheme': 'Mudra Loan Shishu/Kishore for setup', 'skills_needed': 'Teaching, marketing', 'time_to_profit': '1-3 months'},
                {'name': 'Ed-Tech Startup', 'investment': '₹5-25L', 'monthly_potential': '₹2-10L', 'risk': 'high', 'icon': 'devices', 'color': '#E17055', 'tier': 'medium',
                 'description': 'Build an app for regional language education, skill development, or exam prep.', 'govt_scheme': 'Startup India + MeitY Startup Hub grants', 'skills_needed': 'Product design, tech team', 'time_to_profit': '12-18 months'},
            ],
            'Farmer/Agriculture': [
                {'name': 'Organic Farming & Direct Sale', 'investment': '₹1-5L', 'monthly_potential': '₹30K-2L', 'risk': 'moderate', 'icon': 'eco', 'color': '#00B894', 'tier': 'low',
                 'description': 'Organic vegetable/fruit farming with direct-to-consumer model via WhatsApp/social media.', 'govt_scheme': 'Paramparagat Krishi Vikas Yojana — ₹50K/hectare for 3 years', 'skills_needed': 'Organic farming, social media marketing', 'time_to_profit': '3-6 months'},
                {'name': 'Food Processing Unit', 'investment': '₹5-25L', 'monthly_potential': '₹1-5L', 'risk': 'moderate', 'icon': 'factory', 'color': '#E17055', 'tier': 'medium',
                 'description': 'Pickle, jam, juice, spice powder — package farm produce for retail. FSSAI license needed.', 'govt_scheme': 'PM Kisan SAMPADA — 35% subsidy on food processing units', 'skills_needed': 'Food safety, packaging, FSSAI compliance', 'time_to_profit': '6-12 months'},
                {'name': 'Mushroom / Poultry Farming', 'investment': '₹50K-5L', 'monthly_potential': '₹20K-1.5L', 'risk': 'low', 'icon': 'grass', 'color': '#6C5CE7', 'tier': 'low',
                 'description': 'Oyster/button mushroom cultivation or layer/broiler poultry. High demand, quick returns.', 'govt_scheme': 'NABARD subsidy — 25-33% on poultry/mushroom unit', 'skills_needed': 'Basic training (KVIC/NABARD 1-week course)', 'time_to_profit': '2-4 months'},
                {'name': 'Agri-Drone Service', 'investment': '₹5-15L', 'monthly_potential': '₹1-4L', 'risk': 'moderate', 'icon': 'flight', 'color': '#0984E3', 'tier': 'medium',
                 'description': 'Drone spraying service for pesticide/fertilizer. Cover 30-40 acres/day vs 1 acre manual.', 'govt_scheme': 'Sub-Mission on Agri Mechanization — 40-100% subsidy on drones', 'skills_needed': 'Drone pilot license (DGCA), farm knowledge', 'time_to_profit': '3-6 months'},
            ],
            'Business Owner': [
                {'name': 'Export Business (GeM + Amazon Global)', 'investment': '₹5-20L', 'monthly_potential': '₹2-15L', 'risk': 'moderate', 'icon': 'public', 'color': '#6C5CE7', 'tier': 'medium',
                 'description': 'Export Indian products (handicrafts, spices, textiles) via Amazon Global Selling / GeM.', 'govt_scheme': 'MEIS/RoDTEP — 2-5% export incentive + ECGC insurance', 'skills_needed': 'Export documentation, IEC code', 'time_to_profit': '3-6 months'},
                {'name': 'Franchise Business', 'investment': '₹10-50L', 'monthly_potential': '₹2-8L', 'risk': 'low', 'icon': 'storefront', 'color': '#00B894', 'tier': 'high',
                 'description': 'Open franchise of proven brands — Amul, Chai Point, DTDC, Lenskart, etc.', 'govt_scheme': 'Mudra Tarun Loan up to ₹10L for franchise setup', 'skills_needed': 'Management, local market knowledge', 'time_to_profit': '3-9 months'},
                {'name': 'D2C Brand on eCommerce', 'investment': '₹2-10L', 'monthly_potential': '₹1-10L', 'risk': 'high', 'icon': 'shopping_bag', 'color': '#E17055', 'tier': 'medium',
                 'description': 'Launch own brand on Amazon, Flipkart, Meesho. Categories: fashion, beauty, home.', 'govt_scheme': 'ONDC — free listing on govt ecommerce network', 'skills_needed': 'Product sourcing, digital marketing', 'time_to_profit': '3-6 months'},
            ],
            'Government Employee': [
                {'name': 'Rental Income Business', 'investment': '₹10-50L', 'monthly_potential': '₹30K-2L', 'risk': 'low', 'icon': 'apartment', 'color': '#6C5CE7', 'tier': 'high',
                 'description': 'Buy property for rent — PG, co-living, commercial space. Passive income alongside govt job.', 'govt_scheme': 'PMAY subsidy up to ₹2.67L for first home', 'skills_needed': 'Property selection, tenant management', 'time_to_profit': '1-3 months (if property ready)'},
                {'name': 'Agriculture Side Income', 'investment': '₹2-10L', 'monthly_potential': '₹20K-1L', 'risk': 'low', 'icon': 'agriculture', 'color': '#00B894', 'tier': 'medium',
                 'description': 'Farmland investment or contract farming. Tax-free agriculture income!', 'govt_scheme': 'PM Kisan ₹6K/year + NABARD farm loan at 4%', 'skills_needed': 'Farm management or hire manager', 'time_to_profit': '6-12 months'},
            ],
            'Freelancer': [
                {'name': 'Digital Marketing Agency', 'investment': '₹50K-3L', 'monthly_potential': '₹50K-5L', 'risk': 'low', 'icon': 'campaign', 'color': '#E17055', 'tier': 'low',
                 'description': 'SEO, social media, Google Ads management for local businesses. Very high demand.', 'govt_scheme': 'Startup India — ₹10L seed fund if incorporate', 'skills_needed': 'SEO, Google Ads, Meta Ads', 'time_to_profit': '1-3 months'},
                {'name': 'Content Creation Studio', 'investment': '₹1-5L', 'monthly_potential': '₹30K-3L', 'risk': 'low', 'icon': 'videocam', 'color': '#6C5CE7', 'tier': 'low',
                 'description': 'Video production, podcast, and content creation for brands and influencers.', 'govt_scheme': 'Mudra Shishu ₹50K for equipment', 'skills_needed': 'Video editing, storytelling', 'time_to_profit': '1-3 months'},
            ],
            'Banking/Finance': [
                {'name': 'Mutual Fund Distribution', 'investment': '₹1-3L', 'monthly_potential': '₹50K-5L', 'risk': 'low', 'icon': 'trending_up', 'color': '#00B894', 'tier': 'low',
                 'description': 'Become AMFI-registered MFD. Trail commission 0.5-1% on AUM. Passive income builds up.', 'govt_scheme': 'SEBI simplified registration, AMFI exam free retake', 'skills_needed': 'NISM VA certification, client relations', 'time_to_profit': '3-6 months'},
                {'name': 'Insurance Agency', 'investment': '₹50K-2L', 'monthly_potential': '₹30K-3L', 'risk': 'low', 'icon': 'shield', 'color': '#6C5CE7', 'tier': 'low',
                 'description': 'IRDAI licensed insurance agent — life, health, motor. Commission 15-35%.', 'govt_scheme': 'IRDAI POSP license — quick 15hr training', 'skills_needed': 'Sales, relationship management', 'time_to_profit': '1-3 months'},
                {'name': 'Fintech Startup', 'investment': '₹10-50L', 'monthly_potential': '₹2-20L', 'risk': 'high', 'icon': 'account_balance', 'color': '#E17055', 'tier': 'high',
                 'description': 'UPI app, lending platform, or neo-banking for underserved segments.', 'govt_scheme': 'RBI Sandbox — regulatory support for fintech innovation', 'skills_needed': 'Banking domain, tech team, compliance', 'time_to_profit': '12-24 months'},
            ],
            'Chartered Accountant': [
                {'name': 'GST/Tax Filing Service', 'investment': '₹1-3L', 'monthly_potential': '₹1-8L', 'risk': 'low', 'icon': 'receipt', 'color': '#00B894', 'tier': 'low',
                 'description': 'Automated GST, ITR, TDS filing for 100s of MSMEs. Scale with software.', 'govt_scheme': 'GST Suvidha Provider (GSP) license from GSTN', 'skills_needed': 'CA qualification, Tally/Zoho Books', 'time_to_profit': '1-3 months'},
                {'name': 'Startup CFO-as-a-Service', 'investment': '₹2-5L', 'monthly_potential': '₹2-10L', 'risk': 'low', 'icon': 'analytics', 'color': '#6C5CE7', 'tier': 'medium',
                 'description': 'Part-time CFO for startups — funding prep, compliance, MIS. ₹25-50K/client/month.', 'govt_scheme': 'Startup India — connect with funded startups', 'skills_needed': 'Financial modelling, fundraising knowledge', 'time_to_profit': '1-3 months'},
            ],
            'Engineer': [
                {'name': 'Manufacturing Unit (MSME)', 'investment': '₹10-50L', 'monthly_potential': '₹2-10L', 'risk': 'moderate', 'icon': 'precision_manufacturing', 'color': '#E17055', 'tier': 'high',
                 'description': 'Auto parts, plastic moulding, packaging, electronics assembly. High demand for Make in India.', 'govt_scheme': 'PMEGP 25-35% subsidy + PLI scheme incentives', 'skills_needed': 'Engineering, production management', 'time_to_profit': '6-18 months'},
                {'name': 'Solar Installation Business', 'investment': '₹5-15L', 'monthly_potential': '₹1-5L', 'risk': 'low', 'icon': 'solar_power', 'color': '#FDCB6E', 'tier': 'medium',
                 'description': 'Rooftop solar panel installation for homes and businesses. Govt pushing hard.', 'govt_scheme': 'PM Surya Ghar Yojana — 40-60% subsidy for residential solar', 'skills_needed': 'Electrical knowledge, vendor tie-ups', 'time_to_profit': '3-6 months'},
                {'name': 'EV Charging Station', 'investment': '₹5-25L', 'monthly_potential': '₹1-4L', 'risk': 'moderate', 'icon': 'ev_station', 'color': '#00B894', 'tier': 'medium',
                 'description': 'Set up EV charging points on highways or near malls. Early mover advantage.', 'govt_scheme': 'FAME II — 100% subsidy on charging infra in some states', 'skills_needed': 'Electrical engineering, location scouting', 'time_to_profit': '6-12 months'},
            ],
        }

        # Fallback for professions not listed
        generic_ideas = [
            {'name': 'Water Purifier / RO Plant', 'investment': '₹3-15L', 'monthly_potential': '₹50K-3L', 'risk': 'low', 'icon': 'water_drop', 'color': '#0984E3', 'tier': 'low',
             'description': '20L can water delivery business. Every office and home needs it.', 'govt_scheme': 'PMEGP — up to 35% subsidy', 'skills_needed': 'Basic operations, delivery logistics', 'time_to_profit': '3-6 months'},
            {'name': 'Cloud Kitchen / Food Delivery', 'investment': '₹3-10L', 'monthly_potential': '₹50K-3L', 'risk': 'moderate', 'icon': 'restaurant', 'color': '#E17055', 'tier': 'low',
             'description': 'Delivery-only restaurant on Swiggy/Zomato. No dine-in cost. Test multiple brands from one kitchen.', 'govt_scheme': 'Mudra Kishore ₹5L for kitchen setup + FSSAI license', 'skills_needed': 'Cooking/chef hire, Swiggy/Zomato onboarding', 'time_to_profit': '2-4 months'},
            {'name': 'LED Bulb / Paper Cup Manufacturing', 'investment': '₹5-15L', 'monthly_potential': '₹1-4L', 'risk': 'low', 'icon': 'lightbulb', 'color': '#FDCB6E', 'tier': 'medium',
             'description': 'Small manufacturing unit — machines cost ₹3-8L. Sell to local shops + GeM portal.', 'govt_scheme': 'PMEGP 35% subsidy + sell on GeM (govt marketplace)', 'skills_needed': 'Machine operation, quality check', 'time_to_profit': '3-6 months'},
            {'name': 'Laundry / Dry Cleaning Service', 'investment': '₹5-20L', 'monthly_potential': '₹1-3L', 'risk': 'low', 'icon': 'local_laundry_service', 'color': '#A29BFE', 'tier': 'medium',
             'description': 'Pick-up & delivery model. Franchise (UClean, Tumbledry) or independent brand.', 'govt_scheme': 'Mudra Tarun ₹10L for equipment', 'skills_needed': 'Operations management, delivery team', 'time_to_profit': '3-6 months'},
            {'name': 'Mobile/Laptop Repair Hub', 'investment': '₹1-5L', 'monthly_potential': '₹30K-2L', 'risk': 'low', 'icon': 'phonelink_setup', 'color': '#00B894', 'tier': 'low',
             'description': 'Repair + accessories shop. Add refurbished device sales for higher margins.', 'govt_scheme': 'PMKVY training certification — attract customers', 'skills_needed': 'Hardware repair skills or hire technician', 'time_to_profit': '1-3 months'},
        ]

        # Get profession-specific ideas
        profession_key = profession if profession in all_ideas else ''
        profession_ideas = all_ideas.get(profession_key, [])

        # Filter by tier (investment capacity)
        def matches_tier(idea):
            if tier == 'high':
                return True
            elif tier == 'medium':
                return idea['tier'] in ('low', 'medium')
            else:
                return idea['tier'] == 'low'

        filtered_profession_ideas = [i for i in profession_ideas if matches_tier(i)]
        filtered_generic_ideas = [i for i in generic_ideas if matches_tier(i)]

        # Score and rank ideas based on user profile
        def score_idea(idea):
            s = 50  # base score
            # Risk match
            idea_risk = idea.get('risk', 'moderate')
            if idea_risk == risk_appetite:
                s += 20
            elif (risk_appetite == 'high' and idea_risk == 'moderate') or (risk_appetite == 'moderate' and idea_risk == 'low'):
                s += 10
            # Age factor
            if age and age < 30 and idea_risk in ('moderate', 'high'):
                s += 10  # Young = can take more risk
            elif age and age > 50 and idea_risk == 'low':
                s += 15  # Older = prefer safety
            # Salary factor
            if monthly_salary > 100000 and idea['tier'] in ('medium', 'high'):
                s += 10
            return s

        for idea in filtered_profession_ideas:
            idea['score'] = score_idea(idea)
            idea['match_type'] = 'profession'
        for idea in filtered_generic_ideas:
            idea['score'] = score_idea(idea)
            idea['match_type'] = 'general'

        filtered_profession_ideas.sort(key=lambda x: x['score'], reverse=True)
        filtered_generic_ideas.sort(key=lambda x: x['score'], reverse=True)

        # AI summary
        if not profession:
            profile_summary = 'Set your Profession and State in Profile to get personalized business ideas.'
        else:
            profile_summary = f'Based on your profile — {profession}, ₹{monthly_salary:,.0f}/month salary, {risk_appetite} risk appetite'
            if state:
                profile_summary += f', {state}'
            if investable_capital > 0:
                profile_summary += f', ₹{investable_capital:,.0f} investable capital'
            profile_summary += f' — here are your top business ideas.'

        return {
            'profession_ideas': filtered_profession_ideas,
            'general_ideas': filtered_generic_ideas[:5],
            'central_schemes': central_schemes,
            'state_info': state_info,
            'state': state or 'India (General)',
            'tier': tier,
            'profile_summary': profile_summary,
            'profession': profession or 'Not Set',
        }

