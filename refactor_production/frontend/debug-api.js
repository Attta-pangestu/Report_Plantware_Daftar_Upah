// Debug API untuk melihat column definitions yang diterima dari backend

async function debugColumnDefinitions() {
  try {
    console.log('🔍 Debug: Fetching column definitions...');
    
    // Login admin
    const loginResponse = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: 'admin',
        password: 'admin'
      })
    });
    
    if (!loginResponse.ok) {
      throw new Error('Login failed');
    }
    
    const loginData = await loginResponse.json();
    const token = loginData.access_token;
    console.log('✅ Login successful');
    
    // Test dengan periode yang ada data (Januari 2024, Gang A1H)
    const month = 1;
    const year = 2024;
    const gangCode = 'A1H';
    
    console.log(`📊 Testing API: /payroll/columns?month=${month}&year=${year}&gang_code=${gangCode}`);
    
    const columnResponse = await fetch(
      `http://localhost:8000/payroll/columns?month=${month}&year=${year}&gang_code=${gangCode}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (!columnResponse.ok) {
      throw new Error(`Column API failed: ${columnResponse.status}`);
    }
    
    const columnData = await columnResponse.json();
    
    console.log('🎯 RAW COLUMN DEFINITIONS FROM BACKEND:');
    console.log(JSON.stringify(columnData, null, 2));
    
    // Cari PREMI section
    const findPremiSection = (cols) => {
      for (const col of cols || []) {
        if (col.headerName === 'PREMI') {
          console.log('✅ PREMI section found:');
          console.log(JSON.stringify(col, null, 2));
          return col;
        }
        if (col.children) {
          const found = findPremiSection(col.children);
          if (found) return found;
        }
      }
      return null;
    };
    
    const findPotonganSection = (cols) => {
      for (const col of cols || []) {
        if (col.headerName === 'POTONGAN') {
          console.log('✅ POTONGAN section found:');
          console.log(JSON.stringify(col, null, 2));
          return col;
        }
        if (col.children) {
          const found = findPotonganSection(col.children);
          if (found) return found;
        }
      }
      return null;
    };
    
    console.log('\n🎯 PREMI SECTION ANALYSIS:');
    findPremiSection(columnData.columns || columnData);
    
    console.log('\n🎯 POTONGAN SECTION ANALYSIS:');
    findPotonganSection(columnData.columns || columnData);
    
  } catch (error) {
    console.error('❌ Debug error:', error);
  }
}

// Run debug
debugColumnDefinitions();
