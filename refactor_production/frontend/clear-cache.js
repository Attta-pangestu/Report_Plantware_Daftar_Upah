// Script untuk clear cache di browser dan memuat ulang data
console.log('🧹 Clearing frontend cache...');

// Clear localStorage
localStorage.clear();
console.log('✅ localStorage cleared');

// Clear sessionStorage  
sessionStorage.clear();
console.log('✅ sessionStorage cleared');

// Reload page
console.log('🔄 Reloading page...');
window.location.reload();
