// 高级交互效果和动画增强

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    initializeInteractiveEffects();
    initializeScrollAnimations();
    initializeParallaxEffects();
});

// 初始化动画系统
function initializeAnimations() {
    // 为所有交互元素添加动画类
    const interactiveElements = document.querySelectorAll('.card, .btn-primary, input, select, textarea');
    interactiveElements.forEach((element, index) => {
        element.classList.add('interactive-element');
        
        // 添加延迟动画
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// 初始化交互效果
function initializeInteractiveEffects() {
    // 磁性按钮效果
    const buttons = document.querySelectorAll('.btn-primary');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function(e) {
            this.style.transform = 'translateY(-2px) scale(1.02)';
        });
        
        button.addEventListener('mouseleave', function(e) {
            this.style.transform = 'translateY(0) scale(1)';
        });
        
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
    
    // 卡片悬停效果增强
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px) scale(1.01)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
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
                
                // 添加延迟动画
                const children = entry.target.querySelectorAll('.form-group, .info-item, .btn-primary');
                children.forEach((child, index) => {
                    setTimeout(() => {
                        child.style.opacity = '1';
                        child.style.transform = 'translateY(0)';
                    }, index * 100);
                });
            }
        });
    }, observerOptions);
    
    // 观察所有卡片
    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });
}

// 视差效果
function initializeParallaxEffects() {
    let ticking = false;
    
    function updateParallax() {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.welcome-section');
        
        parallaxElements.forEach(element => {
            const speed = 0.5;
            const yPos = -(scrolled * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });
        
        ticking = false;
    }
    
    function requestTick() {
        if (!ticking) {
            requestAnimationFrame(updateParallax);
            ticking = true;
        }
    }
    
    window.addEventListener('scroll', requestTick);
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
        animation: slideInUp 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
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

// 可选：启用鼠标跟随效果（注释掉以禁用）
// initializeMouseFollowEffect();

console.log('🎨 高级动画系统已加载');