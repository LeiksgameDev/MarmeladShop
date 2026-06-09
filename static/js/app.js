const csrfToken=()=>document.querySelector('meta[name="csrf-token"]')?.content||'';
const jsonHeaders=()=>({'Content-Type':'application/json','X-CSRFToken':csrfToken()});
const csrfHeaders=()=>({'X-CSRFToken':csrfToken()});
const money=value=>`${Number(value).toLocaleString('ru-RU')} ₽`;
const isAuth=()=>document.body.dataset.auth==='1';
const getCart=()=>JSON.parse(localStorage.getItem('cart')||'[]');
const setCart=cart=>{localStorage.setItem('cart',JSON.stringify(cart));updateCartCount()};
const authModal=document.querySelector('[data-auth-modal]');
function showAuthModal(){authModal?.classList.add('open')}
function hideAuthModal(){authModal?.classList.remove('open')}
function showToast(message){
  let toast=document.querySelector('[data-toast]');
  if(!toast){
    toast=document.createElement('div');
    toast.className='toast';
    toast.dataset.toast='1';
    document.body.appendChild(toast);
  }
  toast.textContent=message;
  toast.classList.add('show');
  clearTimeout(window.toastTimer);
  window.toastTimer=setTimeout(()=>toast.classList.remove('show'),1800);
}
function updateCartCount(){const count=getCart().reduce((sum,item)=>sum+item.qty,0);document.querySelectorAll('[data-cart-count]').forEach(el=>el.textContent=count)}
function addToCart(id,stock){const max=Number(stock||999);const cart=getCart();const item=cart.find(row=>row.id===Number(id));if(item){if(item.qty>=max){alert('Больше этого количества товара нет на складе');return false}item.qty++}else{if(max<=0){alert('Товара нет в наличии');return false}cart.push({id:Number(id),qty:1})}setCart(cart);return true}
document.addEventListener('click',e=>{
  const add=e.target.closest('[data-add]');
  if(add){
    if(!isAuth()){showAuthModal();return}
    if(!addToCart(add.dataset.add,add.dataset.stock))return;
    showToast('Товар добавлен в корзину');
    add.textContent='Добавлено';
    setTimeout(()=>add.textContent='В корзину',900)
  }
  const burger=e.target.closest('[data-burger]');
  if(burger)document.querySelector('[data-nav]').classList.toggle('open');
  if(e.target.closest('[data-close-auth-modal]')||e.target===authModal)hideAuthModal();
});
async function loadCartProducts(){const ids=getCart().map(x=>x.id);if(!ids.length)return[];const res=await fetch('/api/cart/products',{method:'POST',headers:jsonHeaders(),body:JSON.stringify({ids})});return res.json()}
async function renderCart(){const box=document.querySelector('[data-cart-list]');if(!box)return;let cart=getCart();if(!cart.length){box.innerHTML='<div class="empty-box">Корзина пустая</div>';document.querySelector('[data-cart-total]').textContent=money(0);return}const products=await loadCartProducts();cart=cart.map(row=>{const product=products.find(p=>p.id===row.id);if(product&&row.qty>product.quantity)row.qty=product.quantity;return row}).filter(row=>row.qty>0&&products.find(p=>p.id===row.id));setCart(cart);if(!cart.length){box.innerHTML='<div class="empty-box">Корзина пустая</div>';document.querySelector('[data-cart-total]').textContent=money(0);return}let total=0;box.innerHTML=cart.map(row=>{const product=products.find(p=>p.id===row.id);const price=product.discounted_price||product.price;total+=price*row.qty;return `<div class="cart-item"><div><h3>${product.name}</h3><p>${product.weight} · ${money(price)}</p><small>В наличии: ${product.quantity} шт.</small></div><div class="qty-controls"><button data-dec="${row.id}">−</button><b>${row.qty}</b><button data-inc="${row.id}" ${row.qty>=product.quantity?'disabled':''}>+</button></div><b>${money(price*row.qty)}</b></div>`}).join('');document.querySelector('[data-cart-total]').textContent=money(total)}
document.addEventListener('click',async e=>{
  const inc=e.target.closest('[data-inc]');
  const dec=e.target.closest('[data-dec]');
  if(inc||dec){const id=Number((inc||dec).dataset.inc||(inc||dec).dataset.dec);let cart=getCart();const item=cart.find(x=>x.id===id);if(item){if(inc){const products=await loadCartProducts();const product=products.find(p=>p.id===id);if(product&&item.qty>=product.quantity){alert('Больше этого количества товара нет на складе');return}item.qty++}else{item.qty--}if(item.qty<=0)cart=cart.filter(x=>x.id!==id);setCart(cart);await renderCart()}}
  const order=e.target.closest('[data-create-order]');
  if(order){const res=await fetch('/api/order',{method:'POST',headers:jsonHeaders(),body:JSON.stringify({cart:getCart()})});const data=await res.json();if(data.ok){localStorage.removeItem('cart');location.href=data.url}else{alert(data.message||'Не удалось оформить заказ')}}
  const cancel=e.target.closest('[data-cancel-order]');
  if(cancel){if(!confirm('Отменить заказ?'))return;const res=await fetch(`/api/order/${cancel.dataset.cancelOrder}/cancel`,{method:'POST',headers:csrfHeaders()});const data=await res.json();if(data.ok){document.querySelector('[data-order-status]').textContent='отменен';cancel.remove()}else{alert(data.message||'Не удалось отменить заказ')}}
});
document.querySelectorAll('[data-tab]').forEach(tab=>tab.addEventListener('click',()=>{document.querySelectorAll('[data-tab]').forEach(t=>t.classList.remove('active'));document.querySelectorAll('[data-form]').forEach(f=>f.classList.remove('active'));tab.classList.add('active');document.querySelector(`[data-form="${tab.dataset.tab}"]`).classList.add('active')}));
document.querySelectorAll('[data-toggle-password]').forEach(btn=>btn.addEventListener('click',()=>{const input=btn.parentElement.querySelector('input');input.type=input.type==='password'?'text':'password';btn.textContent=input.type==='password'?'◉':'◎'}));
document.querySelectorAll('[data-phone-mask]').forEach(input=>{if(window.IMask){IMask(input,{mask:'+{7} (000) 000-00-00',lazy:false})}});
updateCartCount();
renderCart();
const autoFilterForm=document.querySelector('[data-auto-filter]');
if(autoFilterForm){
  let filterTimer;
  const submitFilters=()=>autoFilterForm.requestSubmit ? autoFilterForm.requestSubmit() : autoFilterForm.submit();
  autoFilterForm.querySelectorAll('select').forEach(el=>el.addEventListener('change',submitFilters));
  autoFilterForm.querySelectorAll('input[type="search"]').forEach(el=>el.addEventListener('input',()=>{clearTimeout(filterTimer);filterTimer=setTimeout(submitFilters,450)}));
}
document.addEventListener('click',e=>{
  const thumb=e.target.closest('[data-product-thumb]');
  if(!thumb)return;
  const main=document.querySelector('[data-main-product-image]');
  if(main){main.src=thumb.dataset.productThumb;document.querySelectorAll('[data-product-thumb]').forEach(t=>t.classList.remove('active'));thumb.classList.add('active')}
});


document.querySelectorAll('[data-admin-flag]').forEach(input=>{
  input.addEventListener('change',async()=>{
    const productId=input.dataset.productId;
    const row=input.closest('tr');
    const inAssortment=row.querySelector('[data-flag="in_assortment"]')?.checked||false;
    const isNew=row.querySelector('[data-flag="is_new"]')?.checked||false;
    const status=document.querySelector(`[data-save-status="${productId}"]`);
    const previous=input.checked;

    if(status)status.textContent='Сохранение...';
    input.disabled=true;

    try{
      const res=await fetch(`/admin/products/${productId}/flags`,{
        method:'POST',
        headers:{...jsonHeaders(),'X-Requested-With':'XMLHttpRequest'},
        body:JSON.stringify({in_assortment:inAssortment,is_new:isNew})
      });
      const data=await res.json();
      if(!res.ok||!data.ok)throw new Error(data.message||'Ошибка сохранения');
      if(status)status.textContent='Сохранено';
      setTimeout(()=>{if(status)status.textContent=''},1200);
    }catch(err){
      input.checked=!previous;
      if(status)status.textContent='Ошибка';
      alert('Не удалось сохранить флажок. Попробуйте ещё раз.');
    }finally{
      input.disabled=false;
    }
  });
});


document.querySelectorAll('[data-image-preview-input]').forEach(input=>{
  input.addEventListener('change',()=>{
    const preview=document.querySelector('[data-image-preview]');
    if(!preview)return;

    preview.innerHTML='';
    const files=Array.from(input.files||[]);

    if(!files.length){
      preview.innerHTML='';
      return;
    }

    const title=document.createElement('p');
    title.className='preview-title';
    title.textContent=`Выбрано изображений: ${files.length}`;
    preview.appendChild(title);

    files.forEach(file=>{
      if(!file.type.startsWith('image/'))return;

      const card=document.createElement('div');
      card.className='admin-image-card preview-card';

      const img=document.createElement('img');
      img.src=URL.createObjectURL(file);
      img.onload=()=>URL.revokeObjectURL(img.src);

      const name=document.createElement('small');
      name.textContent=file.name;

      card.appendChild(img);
      card.appendChild(name);
      preview.appendChild(card);
    });
  });
});


document.querySelectorAll('[data-dirty-form]').forEach(form=>{
  let isDirty=false;
  form.querySelectorAll('input, textarea, select').forEach(el=>{
    el.addEventListener('change',()=>{isDirty=true});
    el.addEventListener('input',()=>{isDirty=true});
  });
  form.addEventListener('submit',()=>{isDirty=false});
  window.addEventListener('beforeunload',e=>{
    if(!isDirty)return;
    e.preventDefault();
    e.returnValue='';
  });
});
