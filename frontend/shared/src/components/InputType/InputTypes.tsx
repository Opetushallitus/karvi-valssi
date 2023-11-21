enum InputTypes {
    // Monivalinta / Multi select options:
    checkbox = 'checkbox',
    radio = 'radiobutton',
    dropdown = 'dropdown',
    // Teksti- tai numerokenttä / Text or numeric field options:
    singletext = 'singletext',
    multiline = 'multiline',
    numeric = 'numeric',
    email = 'email',
    // Matriisi / Matrix question options:
    matrix_slider = 'matrix_sliderscale',
    matrix_radio = 'matrix_radiobutton',
    // Väliotsikko teksti / static text
    statictext = 'statictext',
}

export const KysymysMatrixTypes = [InputTypes.matrix_slider, InputTypes.matrix_radio];

export const KysymysStringTypes = [
    InputTypes.singletext,
    InputTypes.multiline,
    InputTypes.numeric,
];

export const MonivalintaTypes = [InputTypes.checkbox, InputTypes.radio];

export default InputTypes;
