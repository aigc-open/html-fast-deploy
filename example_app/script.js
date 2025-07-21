document.addEventListener('DOMContentLoaded', function() {
    const demoBtn = document.getElementById('demoBtn');
    const result = document.getElementById('result');
    
    let clickCount = 0;
    
    demoBtn.addEventListener('click', function() {
        clickCount++;
        const messages = [
            '🎉 静态资源加载成功！',
            '🚀 JavaScript 功能正常！',
            '💫 交互效果完美！',
            '🌟 应用运行良好！',
            '🎊 所有功能都正常工作！'
        ];
        
        const message = messages[Math.min(clickCount - 1, messages.length - 1)];
        result.innerHTML = `
            <strong>点击次数:</strong> ${clickCount}<br>
            <strong>状态:</strong> ${message}
        `;
        
        // 添加动画效果
        result.style.animation = 'none';
        result.offsetHeight; // 触发重排
        result.style.animation = 'fadeIn 0.5s ease';
    });
    
    // 添加CSS动画
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);
    
    // 页面加载完成后的欢迎信息
    setTimeout(() => {
        result.innerHTML = '<strong>欢迎使用静态资源演示应用！</strong><br>点击上方按钮测试交互功能。';
    }, 1000);
}); 