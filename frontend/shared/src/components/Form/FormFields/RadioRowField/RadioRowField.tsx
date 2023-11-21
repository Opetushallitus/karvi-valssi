import {ChangeEventHandler} from 'react';
import Grid from '@mui/material/Grid';
import FormControl from '@mui/material/FormControl';
import {Box} from '@mui/material';
import RadioGroup from '@mui/material/RadioGroup';
import Radio from '@mui/material/Radio';
import {FieldValues, UseFormRegister} from 'react-hook-form';
import {GenericFormValueType, MatrixType} from '@cscfi/shared/services/Data/Data-service';
import MatrixEosCheckbox from '../Matrix/MatrixEosCheckbox';
import MatrixMobileScale from '../Matrix/MatrixMobileScale';
import MatrixLabel from '../Matrix/MatrixLabel';
import styles from '../../Form.module.css';

interface RadioRowFieldProps {
    id: string;
    label: string;
    errors?: FieldValues;
    onChange: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
    matrixType: MatrixType;
    value?: number;
    required?: boolean;
    allowEos?: boolean;
    description?: string;
    hidden?: boolean;
    register: UseFormRegister<GenericFormValueType>;
}

function RadioRowField({
    id,
    label,
    errors,
    onChange,
    matrixType,
    value,
    required = false,
    allowEos = false,
    description,
    hidden = false,
    register,
}: RadioRowFieldProps) {
    const marks = matrixType.scale;
    const {ref} = register(id);

    return (
        <FormControl
            key={id}
            ref={ref}
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
                />
                <MatrixMobileScale marks={marks} />
                <Grid
                    item
                    container
                    width={{xs: '100%', md: '65%'}}
                    className={errors ? 'overall-error' : ''}
                    sx={{
                        alignContent: 'flex-start',
                    }}
                >
                    <RadioGroup
                        value={null}
                        name={id}
                        onChange={onChange}
                        sx={{
                            display: 'flex',
                            gap: '1rem',
                            width: '100%',
                            margin: '0.7rem 0 0 0',
                        }}
                    >
                        <Box
                            sx={{
                                display: 'flex',
                                gap: '1rem',
                                height: '100%',
                            }}
                        >
                            {matrixType.scale.map((j) => (
                                <Box
                                    key={j.value}
                                    sx={{
                                        display: 'flex',
                                        width: '100%',
                                        justifyContent: 'center',
                                    }}
                                >
                                    <Radio
                                        className={hidden ? `hidden` : ''}
                                        checked={j.value.toString() === value?.toString()}
                                        value={j.value}
                                        onClick={(event: any) => {
                                            if (event.target.checked && !required) {
                                                onChange({
                                                    ...event,
                                                    currentTarget: {
                                                        name: id,
                                                        value: undefined,
                                                    },
                                                });
                                            }
                                        }}
                                    />
                                </Box>
                            ))}
                        </Box>
                    </RadioGroup>
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

export default RadioRowField;
