"""
Message Formatters - Format signals for Telegram
"""
from datetime import datetime, timezone
from typing import Dict
from telegram.constants import ParseMode


class MessageFormatters:
    """Format trading signals for Telegram messages"""
    
    @staticmethod
    def _format_price(price: float) -> str:
        """فرمت هوشمند قیمت بر اساس مقدار"""
        if price == 0:
            return "$0.00"
        elif price < 0.00001:
            return f"${price:.8f}"
        elif price < 0.001:
            return f"${price:.6f}"
        elif price < 1:
            return f"${price:.4f}"
        elif price < 100:
            return f"${price:.2f}"
        else:
            return f"${price:,.2f}"
    
    @staticmethod
    def format_signal(signal: Dict) -> str:
        """Format signal - main entry point"""
        # Try detailed format first, fallback to summary
        if 'market_data' in signal:
            return MessageFormatters.format_signal_detailed(signal, signal)
        else:
            return MessageFormatters.format_signal_simple(signal)
    
    @staticmethod
    def format_signal_simple(signal: Dict) -> str:
        """Simple signal format"""
        signal_type = signal.get('signal', 'NO_TRADE')
        emoji = "🟢" if signal_type == 'LONG' else "🔴" if signal_type == 'SHORT' else "⚪"
        
        msg = f"{emoji} <b>{signal.get('symbol', 'N/A')} - سیگنال معاملاتی</b>\n\n"
        msg += f"<b>سیگنال:</b> {signal_type}\n"
        msg += f"<b>قیمت:</b> {MessageFormatters._format_price(signal.get('current_price', 0))}\n"
        
        if 'position' in signal and 'entry_zone' in signal['position']:
            entry = signal['position']['entry_zone'].get('optimal', 0)
            msg += f"<b>ورود:</b> {MessageFormatters._format_price(entry)}\n"
        
        if 'position' in signal and 'stop_loss' in signal['position']:
            sl = signal['position']['stop_loss'].get('price', 0)
            msg += f"<b>حد ضرر:</b> {MessageFormatters._format_price(sl)}\n"
        
        if 'position' in signal and 'take_profit' in signal['position']:
            tp_data = signal['position']['take_profit']
            if isinstance(tp_data, list) and len(tp_data) > 0:
                msg += f"<b>اهداف:</b>\n"
                for tp in tp_data[:3]:
                    msg += f"  TP{tp.get('target', 0)}: {MessageFormatters._format_price(tp.get('price', 0))}\n"
        
        return msg
    
    @staticmethod
    def format_signal_summary(market_data: Dict, signal: Dict) -> str:
        """Format short summary message"""
        md = market_data['market_data']
        signal_type = signal.get('signal', 'NO_TRADE')
        
        # Emoji and text
        if signal_type == 'LONG':
            emoji = "🟢"
            signal_text = "LONG"
        elif signal_type == 'SHORT':
            emoji = "🔴"
            signal_text = "SHORT"
        else:
            emoji = "⚪"
            signal_text = "NO_TRADE"
        
        symbol = signal.get('symbol', md['symbol']).replace('USDT', '')
        
        # Trade type
        if 'position' in signal and 'type' in signal['position']:
            pos_type = signal['position']['type']
            leverage = signal['position'].get('leverage', 1)
            
            if pos_type == 'SPOT':
                trade_type = "🟡 spot"
            elif pos_type == 'LEVERAGED' or leverage > 1:
                trade_type = f"⚡ leverage {leverage}x"
            else:
                trade_type = "🟡 spot"
        else:
            trade_type = "🟡 spot"
        
        msg = f"""{emoji}<b>{signal_text}</b>
📉<b>{symbol} /USDT</b>

{trade_type}

"""
        
        # Entry
        if 'position' in signal and 'entry_zone' in signal['position']:
            entry_zone = signal['position']['entry_zone']
            optimal = entry_zone.get('optimal', 0)
            acceptable = entry_zone.get('acceptable', [])
            
            if optimal > 0:
                msg += f"📍 <b>Entry</b> : {MessageFormatters._format_price(optimal).replace('$', '')}\n"
                if acceptable and len(acceptable) >= 2:
                    msg += f"📊 <b>Entry Range</b> : {MessageFormatters._format_price(acceptable[0]).replace('$', '')} - {MessageFormatters._format_price(acceptable[1]).replace('$', '')}\n"
                msg += "\n"
        
        # Targets
        if 'position' in signal and 'take_profit' in signal['position']:
            tp_data = signal['position']['take_profit']
            
            if isinstance(tp_data, list):
                for tp_obj in tp_data:
                    if 'price' in tp_obj:
                        target_num = tp_obj.get('target', 0)
                        price = tp_obj['price']
                        percentage = tp_obj.get('percentage', '')
                        
                        if percentage:
                            msg += f"✔️<b>TP{target_num}</b> : {MessageFormatters._format_price(price).replace('$', '')} ({percentage}%)\n"
                        else:
                            msg += f"✔️<b>TP{target_num}</b> : {MessageFormatters._format_price(price).replace('$', '')}\n"
            elif isinstance(tp_data, dict):
                tp_keys = ['primary', 'secondary', 'tertiary', 'fourth', 'fifth', 'sixth']
                for i, key in enumerate(tp_keys, 1):
                    if key in tp_data and tp_data[key] > 0:
                        msg += f"✔️<b>TP{i}</b> : {MessageFormatters._format_price(tp_data[key]).replace('$', '')}\n"
        
        # Stop Loss
        if 'position' in signal and 'stop_loss' in signal['position']:
            sl = signal['position']['stop_loss']
            sl_price = sl.get('price', 0)
            if sl_price > 0:
                msg += f"❌<b>SL</b> : {MessageFormatters._format_price(sl_price).replace('$', '')}\n"
        
        return msg
    
    @staticmethod
    def format_signal_detailed(market_data: Dict, signal: Dict) -> str:
        """Format detailed signal message"""
        md = market_data['market_data']
        ms = market_data['market_structure']
        ind = market_data['indicators']
        
        signal_type = signal.get('signal', 'NO_TRADE')
        emoji = "🟢" if signal_type == 'LONG' else "🔴" if signal_type == 'SHORT' else "⚪"
        
        signal_fa = {'LONG': 'خرید (لانگ)', 'SHORT': 'فروش (شورت)', 'NO_TRADE': 'بدون معامله'}.get(signal_type, 'بدون معامله')
        
        msg = f"""
{emoji} <b>{signal.get('symbol', md['symbol'])} - تحلیل ICT</b>

💰 <b>قیمت فعلی:</b> {MessageFormatters._format_price(md['current_price'])}
⏰ <b>زمان:</b> {signal.get('timestamp', datetime.now(timezone.utc).isoformat())}

━━━━━━━━━━━━━━━━━━━━━━
<b>🎯 سیگنال معاملاتی</b>

<b>سیگنال:</b> {signal_fa}
<b>درجه سیگنال:</b> {signal.get('signal_grade', 'N/A')}
<b>نوع استراتژی:</b> {signal.get('strategy_type', 'N/A')}

"""
        
        # Context
        if 'context' in signal:
            msg += MessageFormatters._format_context(signal['context'])
        
        # Position
        if 'position' in signal:
            msg += MessageFormatters._format_position(signal['position'])
        
        # Risk Metrics
        if 'risk_metrics' in signal:
            msg += MessageFormatters._format_risk_metrics(signal['risk_metrics'])
        
        # Invalidation
        if 'invalidation_conditions' in signal:
            msg += MessageFormatters._format_invalidation(signal['invalidation_conditions'])
        
        # Trade Management
        if 'trade_management' in signal:
            msg += MessageFormatters._format_trade_management(signal['trade_management'])
        
        # Market Summary
        msg += f"""
━━━━━━━━━━━━━━━━━━━━━━
<b>📈 خلاصه بازار</b>

<b>روند:</b> {ms['htf_trend']} (HTF) | {ms['ltf_trend']} (LTF)
<b>RSI:</b> {ind['rsi']:.1f}
<b>ATR:</b> {MessageFormatters._format_price(ind['atr'])}
"""
        
        if ms['last_mss']['type'] != 'NONE':
            msg += f"<b>MSS:</b> {ms['last_mss']['type']} @ {MessageFormatters._format_price(ms['last_mss']['price'])}\n"
        
        # Persian Summary
        if 'persian_summary' in signal:
            msg += MessageFormatters._format_persian_summary(signal['persian_summary'])
        
        msg += f"\n⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        return msg
    
    @staticmethod
    def _format_context(ctx: Dict) -> str:
        msg = f"""━━━━━━━━━━━━━━━━━━━━━━
<b>📊 زمینه بازار</b>

<b>وضعیت بازار:</b> {ctx.get('market_context', 'N/A')}
"""
        if 'htf_bias' in ctx:
            htf = ctx['htf_bias']
            msg += f"<b>گرایش HTF:</b> {htf.get('direction', 'N/A')} ({htf.get('strength', 'N/A')}) - وزن: {htf.get('weight', 0)}\n"
        
        msg += f"<b>محرک اصلی:</b> {ctx.get('primary_driver', 'N/A')}\n"
        
        if 'liquidity_targets' in ctx and ctx['liquidity_targets']:
            msg += f"\n<b>🎯 اهداف نقدینگی:</b>\n"
            for liq in ctx['liquidity_targets'][:3]:
                msg += f"• {liq.get('type', 'N/A')}: {MessageFormatters._format_price(liq.get('price', 0))} "
                msg += f"({liq.get('strength', 'N/A')}, فاصله: {liq.get('distance_atr', 0)} ATR)\n"
        
        if 'strategic_advantage' in ctx:
            adv = ctx['strategic_advantage']
            msg += f"\n<b>💪 مزیت استراتژیک:</b>\n"
            msg += f"• قدرت کلیدی: {adv.get('key_strength', 'N/A')}\n"
            if 'compromises' in adv and adv['compromises']:
                msg += f"• معایب: {', '.join(adv['compromises'])}\n"
            msg += f"• قابلیت کلی: {adv.get('overall_viability', 'N/A')}\n"
        
        return msg
    
    @staticmethod
    def _format_position(pos: Dict) -> str:
        msg = f"""
━━━━━━━━━━━━━━━━━━━━━━
<b>💼 جزئیات پوزیشن</b>

<b>نوع:</b> {pos.get('type', 'N/A')}
<b>لوریج:</b> {pos.get('leverage', 1)}x
<b>استراتژی ورود:</b> {pos.get('entry_strategy', 'N/A')}
"""
        
        if 'entry_zone' in pos:
            entry = pos['entry_zone']
            msg += f"\n<b>🎯 ناحیه ورود:</b>\n"
            msg += f"• بهینه: {MessageFormatters._format_price(entry.get('optimal', 0))}\n"
            if 'acceptable' in entry and entry['acceptable']:
                msg += f"• محدوده قابل قبول: {MessageFormatters._format_price(entry['acceptable'][0])} - {MessageFormatters._format_price(entry['acceptable'][1])}\n"
            msg += f"• نوع ناحیه: {entry.get('zone_type', 'N/A')}\n"
        
        if 'stop_loss' in pos:
            sl = pos['stop_loss']
            msg += f"\n<b>🛑 حد ضرر:</b>\n"
            msg += f"• قیمت: {MessageFormatters._format_price(sl.get('price', 0))}\n"
            msg += f"• فاصله: {sl.get('distance_percent', 0)}%\n"
            if 'reasoning' in sl:
                reasoning = sl['reasoning'][:100].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                msg += f"• دلیل: {reasoning}\n"
        
        if 'take_profit' in pos:
            tp_data = pos['take_profit']
            msg += f"\n<b>🎯 اهداف سود:</b>\n"
            
            if isinstance(tp_data, list):
                for tp_obj in tp_data:
                    if 'price' in tp_obj:
                        target_num = tp_obj.get('target', 0)
                        price = tp_obj['price']
                        percentage = tp_obj.get('percentage', 0)
                        reasoning = tp_obj.get('reasoning', '')
                        
                        msg += f"• <b>TP{target_num}</b>: {MessageFormatters._format_price(price)}"
                        if percentage > 0:
                            msg += f" ({percentage}%)"
                        if reasoning:
                            reasoning_short = reasoning[:60].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            msg += f" - {reasoning_short}"
                        msg += "\n"
            
            elif isinstance(tp_data, dict):
                tp_keys = ['primary', 'secondary', 'tertiary', 'fourth', 'fifth', 'sixth']
                for i, key in enumerate(tp_keys, 1):
                    if key in tp_data and tp_data[key] > 0:
                        msg += f"• <b>TP{i}</b>: {MessageFormatters._format_price(tp_data[key])}\n"
        
        return msg
    
    @staticmethod
    def _format_risk_metrics(risk: Dict) -> str:
        msg = f"""
━━━━━━━━━━━━━━━━━━━━━━
<b>⚖️ معیارهای ریسک</b>

<b>امتیاز استراتژیک:</b> {risk.get('strategic_score', 0)}/10
"""
        
        if 'regime_adjusted_score' in risk:
            msg += f"<b>امتیاز تنظیم رژیم:</b> {risk.get('regime_adjusted_score', 0)}/10\n"
        if 'volatility_adjusted_score' in risk:
            msg += f"<b>امتیاز تنظیم نوسان:</b> {risk.get('volatility_adjusted_score', 0)}/10\n"
        
        msg += f"<b>درجه سیگنال:</b> {risk.get('signal_grade', 'N/A')}\n"
        msg += f"<b>اطمینان:</b> {risk.get('confidence_percent', 0)}%\n"
        
        if 'market_regime' in risk:
            regime = risk['market_regime']
            msg += f"\n<b>🌐 رژیم بازار:</b>\n"
            msg += f"• نوع: {regime.get('type', 'N/A')}\n"
            msg += f"• اطمینان: {regime.get('confidence', 0)*100:.0f}%\n"
            msg += f"• وضعیت نوسان: {regime.get('volatility_state', 'N/A')}\n"
        
        if 'portfolio_impact' in risk:
            portfolio = risk['portfolio_impact']
            msg += f"\n<b>💼 تاثیر پورتفولیو:</b>\n"
            msg += f"• ریسک کل جدید: {portfolio.get('new_total_risk', 0)}%\n"
            msg += f"• استفاده از ریسک: {portfolio.get('risk_utilization', 'N/A')}\n"
            msg += f"• همبستگی: {portfolio.get('position_correlation', 'N/A')}\n"
        
        if 'key_strengths' in risk and risk['key_strengths']:
            msg += f"\n<b>✅ نقاط قوت:</b> {', '.join(risk['key_strengths'][:3])}\n"
        
        if 'acknowledged_weaknesses' in risk and risk['acknowledged_weaknesses']:
            msg += f"<b>⚠️ نقاط ضعف:</b> {', '.join(risk['acknowledged_weaknesses'][:3])}\n"
        
        if 'strategic_rationale' in risk:
            rationale = risk['strategic_rationale'][:150].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            msg += f"\n<b>💡 منطق استراتژیک:</b>\n{rationale}\n"
        
        return msg
    
    @staticmethod
    def _format_invalidation(inv: Dict) -> str:
        msg = f"""
━━━━━━━━━━━━━━━━━━━━━━
<b>🚫 شرایط ابطال</b>

"""
        if 'structure_break' in inv:
            sb = inv['structure_break']
            msg += f"<b>شکست ساختار:</b> {MessageFormatters._format_price(sb.get('price_level', 0))}\n"
            msg += f"• {sb.get('description', 'N/A')}\n"
        
        if 'time_limit' in inv:
            msg += f"<b>محدودیت زمانی:</b> {inv['time_limit']}\n"
        
        if 'volume_threshold' in inv:
            msg += f"<b>آستانه حجم:</b> {inv['volume_threshold']}\n"
        
        if 'regime_change' in inv:
            msg += f"<b>تغییر رژیم:</b> {inv['regime_change']}\n"
        
        return msg
    
    @staticmethod
    def _format_trade_management(tm: Dict) -> str:
        msg = f"""
━━━━━━━━━━━━━━━━━━━━━━
<b>🔧 مدیریت معامله</b>

<b>سر به سر:</b> {tm.get('breakeven_trigger', 'N/A')}
<b>حداکثر مدت:</b> {tm.get('max_trade_duration', 'N/A')}
"""
        
        if 'trailing_stop' in tm:
            ts = tm['trailing_stop']
            msg += f"\n<b>🎯 استاپ دنباله‌دار:</b>\n"
            msg += f"• فعال‌سازی: {ts.get('activate_after', 'N/A')}\n"
            msg += f"• فاصله: {ts.get('trail_distance', 'N/A')}\n"
            msg += f"• روش: {ts.get('method', 'N/A')}\n"
        
        if 'scale_out_plan' in tm and isinstance(tm['scale_out_plan'], list):
            msg += f"\n<b>📉 برنامه خروج تدریجی:</b>\n"
            for plan in tm['scale_out_plan'][:3]:
                trigger = plan.get('trigger', 'N/A')
                close_pct = plan.get('close_percent', 0)
                action = plan.get('action', 'N/A')
                msg += f"• {trigger}: بستن {close_pct}% → {action}\n"
        
        if 'contingency_plan' in tm:
            msg += f"\n<b>برنامه اضطراری:</b> {tm.get('contingency_plan', 'N/A')}\n"
        
        if 'emergency_exit' in tm:
            msg += f"<b>خروج اضطراری:</b> {tm.get('emergency_exit', 'N/A')}\n"
        
        return msg
    
    @staticmethod
    def _format_persian_summary(ps: Dict) -> str:
        msg = f"""
━━━━━━━━━━━━━━━━━━━━━━
<b>📝 خلاصه فارسی</b>

<b>سیگنال:</b> {ps.get('signal', 'N/A')}
<b>درجه:</b> {ps.get('grade', 'N/A')}
<b>ورود:</b> {ps.get('entry', 'N/A')}
<b>حد ضرر:</b> {ps.get('stop_loss', 'N/A')}
<b>اهداف:</b> {ps.get('targets', 'N/A')}
<b>ریسک:</b> {ps.get('risk', 'N/A')}

<b>دلیل:</b> {ps.get('reasoning', 'N/A')}
"""
        if 'warning' in ps and ps['warning']:
            msg += f"\n<b>⚠️ {ps['warning']}</b>\n"
        
        return msg
