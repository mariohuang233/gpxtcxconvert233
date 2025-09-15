// 埋点统计系统
// 监控页面PV/UV和转换按钮的曝光点击

class Analytics {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.startTime = Date.now();
        this.events = [];
        this.isConvertButtonVisible = false;
        this.hasConvertButtonClicked = false;
        
        this.init();
    }
    
    // 生成会话ID
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // 获取或生成用户ID
    getUserId() {
        let userId = localStorage.getItem('analytics_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('analytics_user_id', userId);
        }
        return userId;
    }
    
    // 初始化埋点系统
    init() {
        // 记录页面访问
        this.trackPageView();
        
        // 监听转换按钮曝光
        this.observeConvertButton();
        
        // 监听转换按钮点击
        this.trackConvertButtonClick();
        
        // 监听页面离开
        this.trackPageLeave();
        
        // 定期发送数据
        this.startPeriodicSend();
        
        console.log('📊 埋点系统已初始化', {
            sessionId: this.sessionId,
            userId: this.userId
        });
    }
    
    // 记录页面访问 (PV)
    trackPageView() {
        const event = {
            type: 'page_view',
            timestamp: Date.now(),
            sessionId: this.sessionId,
            userId: this.userId,
            url: window.location.href,
            referrer: document.referrer,
            userAgent: navigator.userAgent,
            language: navigator.language,
            screenResolution: `${screen.width}x${screen.height}`,
            viewportSize: `${window.innerWidth}x${window.innerHeight}`
        };
        
        this.addEvent(event);
        console.log('📈 页面访问记录', event);
    }
    
    // 监听转换按钮曝光
    observeConvertButton() {
        const convertBtn = document.getElementById('convertBtn');
        if (!convertBtn) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.isConvertButtonVisible) {
                    this.isConvertButtonVisible = true;
                    this.trackConvertButtonExposure();
                }
            });
        }, {
            threshold: 0.5 // 按钮50%可见时触发
        });
        
        observer.observe(convertBtn);
    }
    
    // 记录转换按钮曝光
    trackConvertButtonExposure() {
        const event = {
            type: 'convert_button_exposure',
            timestamp: Date.now(),
            sessionId: this.sessionId,
            userId: this.userId,
            timeFromPageLoad: Date.now() - this.startTime
        };
        
        this.addEvent(event);
        console.log('👁️ 转换按钮曝光', event);
    }
    
    // 监听转换按钮点击
    trackConvertButtonClick() {
        const convertBtn = document.getElementById('convertBtn');
        if (!convertBtn) return;
        
        convertBtn.addEventListener('click', () => {
            if (!this.hasConvertButtonClicked) {
                this.hasConvertButtonClicked = true;
                this.trackConvertButtonClickEvent();
            }
        });
    }
    
    // 记录转换按钮点击
    trackConvertButtonClickEvent() {
        const event = {
            type: 'convert_button_click',
            timestamp: Date.now(),
            sessionId: this.sessionId,
            userId: this.userId,
            timeFromPageLoad: Date.now() - this.startTime,
            timeFromExposure: this.isConvertButtonVisible ? Date.now() - this.getLastEventTime('convert_button_exposure') : null
        };
        
        this.addEvent(event);
        console.log('🖱️ 转换按钮点击', event);
    }
    
    // 监听页面离开
    trackPageLeave() {
        window.addEventListener('beforeunload', () => {
            const event = {
                type: 'page_leave',
                timestamp: Date.now(),
                sessionId: this.sessionId,
                userId: this.userId,
                duration: Date.now() - this.startTime,
                hasClickedConvert: this.hasConvertButtonClicked
            };
            
            this.addEvent(event);
            this.sendEvents(true); // 同步发送
        });
    }
    
    // 添加事件到队列
    addEvent(event) {
        this.events.push(event);
        
        // 如果事件队列过长，立即发送
        if (this.events.length >= 10) {
            this.sendEvents();
        }
    }
    
    // 获取最后一个指定类型事件的时间
    getLastEventTime(eventType) {
        const events = this.events.filter(e => e.type === eventType);
        return events.length > 0 ? events[events.length - 1].timestamp : null;
    }
    
    // 发送事件数据
    sendEvents(sync = false) {
        if (this.events.length === 0) return;
        
        const data = {
            events: [...this.events],
            meta: {
                timestamp: Date.now(),
                userAgent: navigator.userAgent,
                url: window.location.href
            }
        };
        
        // 清空事件队列
        this.events = [];
        
        if (sync) {
            // 同步发送（页面卸载时）
            const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
            navigator.sendBeacon('/api/analytics', blob);
        } else {
            // 异步发送
            fetch('/api/analytics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }).catch(error => {
                console.warn('📊 埋点数据发送失败:', error);
                // 发送失败时重新加入队列
                this.events.unshift(...data.events);
            });
        }
        
        console.log('📤 发送埋点数据', data);
    }
    
    // 定期发送数据
    startPeriodicSend() {
        setInterval(() => {
            this.sendEvents();
        }, 30000); // 每30秒发送一次
    }
    
    // 获取统计摘要
    getSummary() {
        return {
            sessionId: this.sessionId,
            userId: this.userId,
            duration: Date.now() - this.startTime,
            hasConvertButtonExposure: this.isConvertButtonVisible,
            hasConvertButtonClick: this.hasConvertButtonClicked,
            eventsCount: this.events.length
        };
    }
}

// 初始化埋点系统
let analytics;
document.addEventListener('DOMContentLoaded', function() {
    analytics = new Analytics();
    
    // 暴露到全局，方便调试
    window.analytics = analytics;
});

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Analytics;
}