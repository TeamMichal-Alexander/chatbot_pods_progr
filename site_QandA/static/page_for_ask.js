document.getElementById('answer').addEventListener('mouseup', function () {
    const selectedText = window.getSelection();
    const selection = selectedText.toString();
    const isSpecialCharSelected = /\s/.test(selection) && selection.trim() === '';

    if (selection.length > 0 && !isSpecialCharSelected) {
        console.log("Выделенный текст:", selection);
        // Получаем информацию о выделении
        const range = selectedText.getRangeAt(0);
        const rect = range.getBoundingClientRect();  // Получаем позицию выделенного текста

        // Проверка первого символа выделения
        const firstChar = selection.charAt(0);

        // Если выделение начинается с новой строки (например, при тройном клике), поднимем кнопку на одну строку выше
        if (firstChar === '\n') {
            // Сдвиг верхней границы на высоту первой строки
            rect.top += rect.height;
        }

        // Получаем элемент кнопки
        const button = document.getElementById('action-button');

        // Устанавливаем позицию кнопки
        button.style.position = 'absolute';
        button.style.left = `${rect.left + window.scrollX}px`; // По горизонтали
        button.style.top = `${rect.top + window.scrollY - 40}px`; // Над текстом (с небольшим отступом)
        button.style.zIndex = '9999';  // Чтобы кнопка была на переднем плане
        button.style.display = 'block'; // Показываем кнопку
    } else {
        // Если выделены только пробелы или спецсимволы, скрываем кнопку
        const button = document.getElementById('action-button');
        button.style.display = 'none';
    }
});

document.getElementById('answer').addEventListener('selectionchange', function () {
    const selectedText = window.getSelection();
    const selection = selectedText.toString();

    if (selection.length === 0) {
        const button = document.getElementById('action-button');
        const form_improve = document.getElementById('form_improve')

        button.style.display = 'none'; // Скрыть кнопку, если выделение пропало
        form_improve.style.display = 'none'
    }
});


document.getElementById('action-button').addEventListener('click', function () {
    const quotation_text = document.getElementById('quotation_text')
    const quotation = document.getElementById('quotation')
    const button = document.getElementById('action-button');
    const selectedText = window.getSelection();
    const cleanedText = String(selectedText).replace(/\n/g, " ");
    clearSelection();
    // form_improve.style.position = 'absolute';
    // form_improve.style.left = button.style.left
    // form_improve.style.top = button.style.top
    quotation_text.innerText = cleanedText;
    quotation.style.display = 'block';
    button.style.display = 'none';
    // form_improve.style.zIndex = '10000';
    // form_improve.style.display = 'block'
});

document.getElementById('return').addEventListener('click', function () {
    const form_improve = document.getElementById('form_improve')
    const button = document.getElementById('action-button');
    form_improve.style.display = 'none'
    const selectedText = window.getSelection();
    const selection = selectedText.toString();

    if (selection.length === 0) {
        button.style.display = 'none'
    } else {
        button.style.display = 'block'
    }

});


const textarea = document.getElementById('autoResize');

    textarea.addEventListener('input', function() {
    this.style.height = 'auto';  // Сбрасываем высоту
    this.style.height = (this.scrollHeight) + 'px';  // Устанавливаем высоту в зависимости от содержимого
});


function delete_quotation(){
    const quotation_text = document.getElementById('quotation_text')
    const quotation = document.getElementById('quotation')
    quotation_text.innerText = '';
    quotation.style.display = 'none';
}

function clearSelection() {
    if (window.getSelection) {
        const selection = window.getSelection();
        if (selection) {
            selection.removeAllRanges(); // Удаляет все выделенные диапазоны
        }
    } else if (document.selection) { // Для старых браузеров (IE)
        document.selection.empty();
    }
}

document.getElementById('query').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendAjaxRequest();
    }
});
