// 高级交互效果和动画增强

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    initializeInteractiveEffects();
    initializeScrollAnimations();
    initializeParallaxEffects();
    initializeErrorHandling();
    
    // 添加连接桥梁元素
    addConnectionBridge();
});

// 初始化动画系统
function initializeAnimations() {
    // 为所有交互元素添加动画类
    const interactiveElements = document.querySelectorAll('.card, .btn-primary, input, select, textarea');
    interactiveElements.forEach((element, index) => {
        element.classList.add('interactive-element');
        
        // 添加延迟动画 - 性能优化
        requestAnimationFrame(() => {
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 50); // 减少延迟时间
        });
    });
}

// 初始化交互效果
function initializeInteractiveEffects() {
    // 磁性按钮效果 - 性能优化版
    const buttons = document.querySelectorAll('.btn-primary');
    buttons.forEach(button => {
        // 使用节流优化鼠标事件 - 减少频率
        const throttledMouseEnter = throttle(function(e) {
            requestAnimationFrame(() => {
                this.style.transform = 'translateY(-1px) scale(1.01) translateZ(0)';
            });
        }, 32); // 30fps 减少频率
        
        const throttledMouseLeave = throttle(function(e) {
            requestAnimationFrame(() => {
                this.style.transform = 'translateY(0) scale(1) translateZ(0)';
            });
        }, 32);
        
        button.addEventListener('mouseenter', throttledMouseEnter);
        button.addEventListener('mouseleave', throttledMouseLeave);
        
        // 点击波纹效果
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
                z-index: 1;
            `;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // 卡片悬停效果增强 - 性能优化
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        const throttledEnter = throttle(function() {
            requestAnimationFrame(() => {
                this.style.transform = 'translateY(-3px) scale(1.005) translateZ(0)';
            });
        }, 32);
        
        const throttledLeave = throttle(function() {
            requestAnimationFrame(() => {
                this.style.transform = 'translateY(0) scale(1) translateZ(0)';
            });
        }, 32);
        
        card.addEventListener('mouseenter', throttledEnter);
        card.addEventListener('mouseleave', throttledLeave);
    });
    
    // 输入框焦点效果
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.transform = 'translateY(-1px)';
        });
        
        input.addEventListener('blur', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// 滚动动画
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                // 添加延迟动画 - 性能优化
                const children = entry.target.querySelectorAll('.form-group, .info-item, .btn-primary');
                children.forEach((child, index) => {
                    requestAnimationFrame(() => {
                        setTimeout(() => {
                            child.style.opacity = '1';
                            child.style.transform = 'translateY(0)';
                        }, index * 50); // 减少延迟时间
                    });
                });
            }
        });
    }, observerOptions);
    
    // 观察所有卡片
    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });
}

// 视差效果 - 性能优化版
function initializeParallaxEffects() {
    const parallaxElements = document.querySelectorAll('.welcome-section');
    let ticking = false;
    
    // 优化滚动视差效果 - 减少视差强度
    const updateParallax = () => {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.2; // 减少视差强度
        
        parallaxElements.forEach(element => {
            element.style.transform = `translateY(${rate}px) translateZ(0)`;
        });
        ticking = false;
    };
    
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(updateParallax);
            ticking = true;
        }
    }, { passive: true });
    
    // 优化鼠标跟随效果
    const updateMouseEffect = throttle((e) => {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;
        
        parallaxElements.forEach(element => {
            const moveX = (mouseX - 0.5) * 20;
            const moveY = (mouseY - 0.5) * 20;
            element.style.transform = `translateY(${window.pageYOffset * -0.5}px) translate(${moveX}px, ${moveY}px)`;
        });
    }, 16);
    
    document.addEventListener('mousemove', updateMouseEffect, { passive: true });
}

// 添加CSS动画关键帧
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    .animate-in {
        animation: slideInUp 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
    }
    
    /* 平滑滚动 */
    html {
        scroll-behavior: smooth;
    }
    
    /* 减少动画对性能的影响 */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
`;
document.head.appendChild(style);

// 性能优化：节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 鼠标跟随效果（可选）
function initializeMouseFollowEffect() {
    const cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    document.body.appendChild(cursor);
    
    const cursorStyle = `
        .custom-cursor {
            position: fixed;
            width: 20px;
            height: 20px;
            background: radial-gradient(circle, rgba(0, 208, 132, 0.3) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            transition: transform 0.1s ease;
        }
        
        .custom-cursor.hover {
            transform: scale(1.5);
            background: radial-gradient(circle, rgba(0, 208, 132, 0.5) 0%, transparent 70%);
        }
    `;
    
    const cursorStyleSheet = document.createElement('style');
    cursorStyleSheet.textContent = cursorStyle;
    document.head.appendChild(cursorStyleSheet);
    
    document.addEventListener('mousemove', throttle((e) => {
        cursor.style.left = e.clientX - 10 + 'px';
        cursor.style.top = e.clientY - 10 + 'px';
    }, 16));
    
    // 悬停效果
    document.querySelectorAll('button, a, input, select').forEach(element => {
        element.addEventListener('mouseenter', () => cursor.classList.add('hover'));
        element.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
    });
}

// 添加连接桥梁元素的创建逻辑
function addConnectionBridge() {
    const welcomeSection = document.querySelector('.welcome-section');
    if (welcomeSection) {
        // 创建连接桥梁元素
        const bridge = document.createElement('div');
        bridge.className = 'connection-bridge';
        welcomeSection.appendChild(bridge);
        
        // 添加交互式连接点
        const connectionDots = document.createElement('div');
        connectionDots.className = 'connection-dots';
        connectionDots.innerHTML = `
            <div class="dot dot-1"></div>
            <div class="dot dot-2"></div>
            <div class="dot dot-3"></div>
        `;
        welcomeSection.appendChild(connectionDots);
        
        // 添加连接点样式
        const style = document.createElement('style');
        style.textContent = `
            .connection-dots {
                position: absolute;
                bottom: -30px;
                left: 50%;
                transform: translateX(-50%);
                display: flex;
                gap: 8px;
                z-index: 5;
            }
            .dot {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: rgba(0, 208, 132, 0.6);
                animation: dotPulse 2s ease-in-out infinite;
            }
            .dot-2 { animation-delay: 0.3s; }
            .dot-3 { animation-delay: 0.6s; }
            @keyframes dotPulse {
                0%, 100% { opacity: 0.3; transform: scale(1); }
                50% { opacity: 1; transform: scale(1.2); }
            }
        `;
        document.head.appendChild(style);
    }
}

// 可选：启用鼠标跟随效果（注释掉以禁用）
// initializeMouseFollowEffect();

// 开发者信息点击计数功能
let developerClickCount = 0;
const developerInfo = document.getElementById('developerInfo');

if (developerInfo) {
    developerInfo.addEventListener('click', function() {
        developerClickCount++;
        
        // 添加点击反馈效果
        this.style.transform = 'scale(0.95)';
        setTimeout(() => {
            this.style.transform = 'scale(1)';
        }, 100);
        
        // 更新提示文本
        const remaining = 5 - developerClickCount;
        if (remaining > 0) {
            this.title = `还需点击${remaining}次查看统计`;
        } else {
            this.title = '正在跳转到统计页面...';
        }
        
        // 点击5次后跳转到统计页面
        if (developerClickCount >= 5) {
            // 添加成功提示效果
            this.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            this.style.color = 'white';
            this.style.borderRadius = '8px';
            this.style.padding = '5px 10px';
            this.style.transition = 'all 0.3s ease';
            
            setTimeout(() => {
                window.location.href = '/analytics';
            }, 500);
            
            developerClickCount = 0; // 重置计数
        }
    });
}

// 错误处理和健壮性增强
function initializeErrorHandling() {
    // 全局错误处理
    window.addEventListener('error', function(e) {
        console.error('JavaScript错误:', e.error);
        // 可以在这里添加错误上报逻辑
    });
    
    // Promise错误处理
    window.addEventListener('unhandledrejection', function(e) {
        console.error('未处理的Promise错误:', e.reason);
        e.preventDefault();
    });
    
    // 网络请求错误处理
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args)
            .catch(error => {
                console.error('网络请求失败:', error);
                throw error;
            });
    };
}

// 安全的DOM操作函数
function safeQuerySelector(selector) {
    try {
        return document.querySelector(selector);
    } catch (e) {
        console.warn('选择器错误:', selector, e);
        return null;
    }
}

// 安全的事件监听器添加
function safeAddEventListener(element, event, handler) {
    if (element && typeof element.addEventListener === 'function') {
        try {
            element.addEventListener(event, handler);
        } catch (e) {
            console.warn('事件监听器添加失败:', e);
        }
    }
}

console.log('🎨 高级动画系统已加载');
console.log('🔍 隐藏统计功能已激活');
console.log('🛡️ 错误处理系统已激活');