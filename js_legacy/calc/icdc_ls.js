// Insain calculator data controller - loader of structure data v. 2.4

// Объявления для совместимости со старыми и ущербными браузерами
if (!String.prototype.startsWith) {
  Object.defineProperty(String.prototype, 'startsWith', {
	enumerable: false,
	configurable: false,
	writable: false,
	value: function(searchString, position) {
	  position = position || 0;
	  return this.indexOf(searchString, position) === position;
	}
  });
}

if (!String.prototype.isString) {
  Object.defineProperty(String.prototype, 'isString', {
	enumerable: false,
	configurable: false,
	writable: false,
	value: true
  });
}

if (typeof globalThis === 'undefined') {
	if (typeof window !== 'undefined') { var globalThis = window; } 
	else { if (typeof self !== 'undefined') { var globalThis = self; }
	else { if (typeof global !== 'undefined') { var globalThis = global; } }}
}

// Класс Ошибок для обработки внутренних ошибок калькулятора
class ICalcError extends Error {
	constructor(message) {
		super(message);
		this.name = "ICalcError";
	};
}

// Создаём локальное пространство имён для let, const
{

	const mainName = 'insaincalc'; // Define name for the main object
	
	const $Name = mainName+'.common.USD'; // Define name for the USD/RUB rate

	if ( !globalThis[mainName] ) {globalThis[mainName] = {};} // Check if the main object already exists. If not then create
	const _ = globalThis[mainName]; // Declare short pseudonym for the main object

	const unenum = function(obj, key, val) { // Function to create unenumerable property
		Object.defineProperty(obj, key, {
			value: val,
			writable: true,
			enumerable: false,
			configurable: true
		});
	};
		  

	const locked = function(obj, key, val) { // Function to create unenumerable unwritable property
		Object.defineProperty(obj, key, {
			value: val,
			writable: false,
			enumerable: false,
			configurable: true
		});
	};

	// Constructor, создающий объект из строки JSON с дефолтными значениями
	_.StructDat = function (jstring) {

		  let data = JSON.parse(_.delComments(jstring)); // Чистим от комментариев, парсим и добавляем в новый объект

		  let records = {};
		  let indx = 0;
		  
		  if ( !('Default' in data) ) { unenum(data,'Default',{}); } // Если в корне не определен Default, добавляем пустой
		  
		  if (data.Links) { locked(data, 'Links', data.Links); } // If 'Links' were declared make it unenumerable
		  
		  defaulter(data); // Устанавливаем дефолтные значения как прототипы
		  
		  unenum(data, '_records', records);

		  Object.defineProperty(data, '_struct', {
			get: structGetter,
			enumerable: false,
			configurable: true
		  });
		  
		  return data;
			  

		  function defaulter(obj) {

			for (let prp in obj) { // Для всех enumerable свойств
			  
			  if (typeof obj[prp] === 'object'){
					if ('Default' in obj[prp]) { // Если свойство содержит в себе Default, обрабатываем этот Default
												 // и дефолтируем остальные свойства
						obj[prp].Default = recproc(obj, obj[prp].Default);
						Object.defineProperty(obj[prp], 'Default', {enumerable: false}); // Make 'Default' unenumerable

						defaulter(obj[prp]);
					}
					else { // Иначе данное свойство считаем записью и обрабатываем его
						obj[prp] = recproc(obj, obj[prp]); 
						
						records[ obj[prp].ID || ('_generatedID_' + (indx++)) ] = obj[prp]; // и добавляем в список
					}
			  } // Endif checking type
			} // End for cycle

		  } // Endfunction defaulter

		  

		  function recproc(prnt,chld){ // Assigning property values and processing special keynames

			  let record = Object.create(prnt.Default); // Create record with 'Default' prototype
			  
			  for (let prp in chld) { // Process all properties

				  if (prp.startsWith('name')) { // Checking if a key starts with 'name'
					let p = prp;
					let str = chld[prp];
					
					Object.defineProperty(record, prp, {
					  get: nameGetter,
					  set: function(val){return str = val;},
					  enumerable: true,
					  configurable: true
					}); 
					
					// Getter for свойств специального вида 'name...'
					function nameGetter() {
						if ( str.isString && (str.charAt(0) === '+') ) {
							return (Object.getPrototypeOf(this)[p] || '') + str.substring(1);
						}
						else return str;
					} // Endfuncton nameGetter
					
				  } // Endif checking if a key starts with 'name'
				  
				  else if (prp.startsWith('cost') || prp.startsWith('eval')) {  // Checking if a key starts with 'cost' or 'eval'
					let p = prp;
					
					Object.defineProperty(record, prp, {
					  set:evalSetter,
					  enumerable: true,
					  configurable: true
					}); 
					
					record[prp] = chld[prp];
					
					function evalSetter(expr){ // Transform string and define getter function evaluating string as expression
						if (expr.isString) {
							Object.defineProperty(this, p, { get: new Function('return '+decode(expr,p) ) });
						}
						else { Object.defineProperty(this, p, { get: function(){return expr;} }); }
					} // Endfunction evalSetter
					
				  } // Endif checking if a key starts with 'cost' or 'eval'
				  
				  else if (prp.startsWith('calc') && chld[prp].calc) {  // Checking if a key starts with 'calc'
					let p = prp;
					
					if (chld[prp].calc.isString) {
						args = Array.isArray(chld[prp].args) ? chld[prp].args : [];
						args.push('return '+decode(chld[prp].calc,p));
						const calcFunConstr = applyAndNew(Function, args)
						record[prp] = new calcFunConstr();
					}
					else {
						record[prp] = chld[prp];
					}
					
				  } // Endif checking if a key starts with 'calc'
				  
				  else { record[prp] = chld[prp]; }// If this is no special keyname use value as is

			  }

			  return record;
		  } // Endfunction recproc

		  function decode(expr,p){
			  expr = expr.replace(/\$(?=\d)/g,$Name+'*');
			  expr = expr.replace(/#(?=\.)/g,mainName);
			  expr = expr.replace(/\^(?=\.)/g,'this');//(?<!\w)
			  expr = expr.replace(/@(?!\w)/g,'Object.getPrototypeOf(this)[\''+p+'\']');
			  //alert(expr);
			  return expr;
		  }

	  // Метод, возвращающий структуру в текстовом виде (для отладки)
		  function structGetter() {
			  let s = this._source + '\n';
			  let i = 0;
			  struct(this);
			  return s;
			  
			  function struct(obj) {
				  ++i;
				  for (let prp in obj) {
					  let child = obj[prp];
					  for (let k=i;(k--)>0;) {s += ' |-';}
					  if ((typeof child === 'object') && ("Default" in child)) {
						  s += '[grp] '+prp+'\n';
						  struct(obj[prp]);
					  }
					  else {
						  s += '[rec] '+prp+'\n';
					  }
				  }
				  --i;
			  }
		  } // Endfunction structgetter
		  
		  
		  function applyAndNew(constructor, args) {
			  function partial () {
				  return constructor.apply(this, args);
			  }
			  if (typeof constructor.prototype === "object") {
				  partial.prototype = Object.create(constructor.prototype);
			  }
			  return partial;
		  }

	}; // End constructor StructDat

	 _.delComments = function delComments(comstr) {

		 return comstr.replace(/\/\*[^]*\*\//g,'').replace(/\/\/.*/g,'').replace(/,\s*(?=})/g,'');

	 };

	 
	 
	 _.loadStructDat = function loadStructDat(path,name,action) {

		if (!name) { // If 'name' wasn't provided construct it from the filename
			fragm = path.split(/[\/\\]/);
			name = fragm[fragm.length-1].match(/\w*/)[0].toLowerCase();
		}

		if ( (!_[name]) || (_[name]._source.toLowerCase != path.toLowerCase) ) { // Do only if we didn't load this file yet
            
			unenum(_[name]={}, "_source", path); // Create object to store data and write path to '_source' property

			let DatReq = new XMLHttpRequest();
			DatReq.onload = reqListener;
			DatReq.open("get", path, true);
			DatReq.send();
			
			function reqListener () {
				_[name] = new _.StructDat(this.response);
				unenum(_[name], "_source", path); // Write path to '_source' property
				
				if (_[name].Links) { for (let ind in _[name].Links) {_.loadStructDat(_[name].Links[ind]);} }
				
				if (typeof action === "function") {action();}

				//alert(_[name]._struct);
				//if (_.hardplain.Default && _.common.Default && _.film.Default) {
				//	alert(_.hardplain._records.PVC5mm.namedisplayed+'\n'+_.hardplain._records.PVC3mm.namedisplayed);
				//	alert(_.hardplain._records.PVC5mm.cost_milling+'\n'+_.hardplain._records.PVC5mm.cost_sheet);
				//};
				
			} // Endfunction reqListener

		} // End if block '...we didn't load this file yet'

	}; // Endfunction loadStructDat



	_.loadData = function loadData(){

		for (let ind in arguments) {_.loadStructDat(arguments[ind]);}

	};

	_.loadData("icalc/calc/common.json");

} // End of local namespace











