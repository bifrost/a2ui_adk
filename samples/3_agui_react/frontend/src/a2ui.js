// A2UI v1.0 example messages. In production validate against a registered catalog.
export const CATALOG = 'https://example.org/catalogs/accounting/v3.json';
const invoiceRows=[{customer:'Acme ApS',amount:1250,status:'Paid'},{customer:'Beta IVS',amount:850,status:'Unpaid'},{customer:'Gamma ApS',amount:2420,status:'Paid'}];
const sales=[{month:'Jul',amount:12000},{month:'Aug',amount:15000},{month:'Sep',amount:13400},{month:'Oct',amount:18300}];
export const DEMO_DATA={table:{columns:[{key:'customer',label:'Kunde'},{key:'amount',label:'Beløb (DKK)'},{key:'status',label:'Status'}],rows:invoiceRows},card:{title:'Fakturaoverblik',metrics:[{label:'Fakturaer',value:'3'},{label:'Betalt',value:'3.670 DKK'},{label:'Ubetalt',value:'850 DKK'}]},chart:{title:'Omsætning (DKK)',points:sales}};
export function toA2UI(kind, id) {
  if (!Object.hasOwn(DEMO_DATA,kind)) throw new Error('Unregistered component: '+kind);
  const surfaceId='surface-'+id;
  return [
    {version:'v1.0',createSurface:{surfaceId,catalogId:CATALOG}},
    {version:'v1.0',updateComponents:{surfaceId,components:[{id:'root',component:kind==='table'?'Table':kind==='card'?'Card':'Chart',data:{'path':'/payload'}}]}},
    {version:'v1.0',updateDataModel:{surfaceId,path:'/payload',value:DEMO_DATA[kind]}}
  ];
}
export function readSurface(messages) {
  if (!Array.isArray(messages) || messages.length!==3 || messages.some(m=>m.version!=='v1.0')) throw Error('Invalid protocol version');
  const a=messages[0].createSurface,b=messages[1].updateComponents,c=messages[2].updateDataModel;
  if (!a || !b || !c || !a.surfaceId || a.surfaceId!==b.surfaceId || b.surfaceId!==c.surfaceId) throw Error('Surface mismatch');
  if (a.catalogId!==CATALOG || b.components.length!==1 || b.components[0].data?.['path']!=='/payload' || c.path!=='/payload') throw Error('Unknown catalog or binding');
  const type=b.components[0].component;
  if (!['Table','Card','Chart'].includes(type)) throw Error('Unknown component');
  return {type,data:c.value};
}
