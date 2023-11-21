import {ChangeEventHandler, useEffect, useState} from 'react';
import {FieldValues} from 'react-hook-form';
import Slider, {SliderProps} from '@mui/material/Slider';
import Grid from '@mui/material/Grid';
import FormControl from '@mui/material/FormControl';
import {styled} from '@mui/material/styles';
import {MatrixType} from '@cscfi/shared/services/Data/Data-service';
import MatrixEosCheckbox from '../Form/FormFields/Matrix/MatrixEosCheckbox';
import MatrixMobileScale from '../Form/FormFields/Matrix/MatrixMobileScale';
import MatrixLabel from '../Form/FormFields/Matrix/MatrixLabel';
import styles from './SliderField.module.css';

interface SliderFieldProps {
    id: string;
    label: string;
    errors?: FieldValues;
    isSubmitting: boolean;
    firstError: string;
    onChange: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
    matrixType: MatrixType;
    value?: number;
    required?: boolean;
    allowEos?: boolean;
    description?: string;
    hidden?: boolean;
}

interface CustomSliderProps extends SliderProps {
    hideThumb?: boolean;
    dimmThumb?: boolean;
    hidden?: boolean;
}

const CustomSlider = styled(Slider, {
    shouldForwardProp: (prop) => prop !== 'hideThumb' && prop !== 'dimmThumb',
})<CustomSliderProps>(({hideThumb = false, hidden = false}) => ({
    '& .MuiSlider-thumb': {
        height: 24,
        width: 24,
        backgroundColor: hidden || hideThumb ? 'rgba(47, 72, 127, 0)' : '#2F3C71',
        visibility: hidden || hideThumb ? 'hidden' : 'unset',
    },
    '& span.MuiSlider-thumb::before': {
        boxShadow: (hidden || hideThumb) && 'none',
    },
    '& .MuiSlider-track': {
        opacity: hideThumb ? 0 : 1,
        color: hidden ? '#808080' : '#2F3C71',
    },
    '& .MuiSlider-rail': {
        opacity: 1,
        color: hidden ? '#808080' : '#BCBCBC',
    },
    '& .MuiSlider-mark': {
        backgroundColor: hidden ? '#808080' : '#BCBCBC',
        height: 16,
        width: 2,
        '&.MuiSlider-markActive': {
            opacity: 1,
            // eslint-disable-next-line no-nested-ternary
            backgroundColor: hidden ? '#808080' : hideThumb ? '#BCBCBC' : '#2F3C71',
        },
    },
}));

const onChangeEvent = (
    event: any,
    id: string,
    newValue: number | string | undefined,
) => ({
    ...event,
    currentTarget: {
        name: id,
        // @ts-ignore
        value: newValue,
    },
});

function SliderField({
    id,
    label,
    errors,
    isSubmitting = false,
    firstError = 'none',
    onChange,
    matrixType,
    value,
    required = false,
    allowEos = false,
    description,
    hidden = false,
}: SliderFieldProps) {
    const marks = matrixType.scale;
    const [labelFocus, setLabelFocus] = useState<boolean>(false);

    useEffect(() => {
        // Workaround, as RHF 'criteriaMode' does not focus on error in this component.
        if (isSubmitting && firstError === id) {
            const inputElement: HTMLInputElement = document.querySelector(
                `input[name="${id}"]`,
            );
            if (inputElement) {
                inputElement.focus();
            }
        }
    }, [firstError, id, isSubmitting]);

    return (
        <FormControl
            key={id}
            component="fieldset"
            className={styles['input-field']}
            sx={{
                display: 'grid',
            }}
        >
            <Grid
                container
                direction={{xs: 'column', sm: 'row'}}
                columns={{xs: 1, sm: 3}}
            >
                <MatrixLabel
                    label={label}
                    required={required}
                    description={description}
                    errors={errors}
                    focused={labelFocus}
                />
                <MatrixMobileScale marks={marks} />
                <Grid
                    item
                    width={{xs: '100%', md: '65%'}}
                    sx={{
                        margin: '1.2rem 0 0 0',
                        alignContent: 'center',
                    }}
                    padding={{md: '0 4rem'}}
                    className={errors ? 'overall-error' : ''}
                >
                    <CustomSlider
                        id={id}
                        name={id}
                        className={styles['slider-root']}
                        valueLabelDisplay="off"
                        onFocus={() => setLabelFocus(true)}
                        onBlur={() => setLabelFocus(false)}
                        onChange={(event, newValue) =>
                            onChange(
                                onChangeEvent(
                                    event,
                                    id,
                                    Array.isArray(newValue) ? newValue[0] : newValue,
                                ),
                            )
                        }
                        marks
                        step={1}
                        value={value || null /* matrixType.default_value */}
                        hideThumb={value === undefined || value === -1}
                        min={marks[0].value as number}
                        max={marks[marks.length - 1].value as number}
                        hidden={hidden}
                    />
                </Grid>
                {allowEos && (
                    <MatrixEosCheckbox
                        id={id}
                        onChange={onChange}
                        matrixType={matrixType}
                        value={value}
                    />
                )}
            </Grid>
        </FormControl>
    );
}

export default SliderField;
