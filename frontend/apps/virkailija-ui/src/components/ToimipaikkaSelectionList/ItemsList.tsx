import {Dispatch, SetStateAction, useMemo, useState} from 'react';
import {useTranslation} from 'react-i18next';
import GenericTextField from '@cscfi/shared/components/GenericTextField/GenericTextField';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import IndeterminateCheckBoxOutlinedIcon from '@mui/icons-material/IndeterminateCheckBoxOutlined';
import Checkbox from '@mui/material/Checkbox';
import CheckIcon from '@mui/icons-material/Check';
import ExpandMoreRounded from '@mui/icons-material/ExpandMore';
import AccordionSummary from '@mui/material/AccordionSummary';
import Accordion from '@mui/material/Accordion';
import {AccordionDetails} from '@mui/material';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import {
    OppilaitosSetType,
    OppilaitosGroupType,
    OppilaitosType,
    AlueFormType,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import EditIcon from '@mui/icons-material/Edit';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import {UseFormReturn} from 'react-hook-form';
import styles from './ToimipaikkaSelectionList.module.css';
import {filterItems, itemsIntersection} from './utils';
import {
    flattenItems,
    getDefaultEmptySet,
    itemsLength,
    sortItems,
} from '../../utils/helpers';

interface ItemsListProps {
    isLeft: boolean;
    label?: string;
    allItems?: OppilaitosSetType;
    disabled?: boolean;
    filter: string;
    setFilter: Dispatch<SetStateAction<string>>;
    checked: OppilaitosSetType;
    setChecked: Dispatch<SetStateAction<OppilaitosSetType>>;
    itemsInGroups?: boolean;
    labelModifiable?: boolean;
    selectableGroups: boolean;
    formMethods?: UseFormReturn<AlueFormType, any, undefined>;
}

const oppilaitosItem = (
    oppilaitos: OppilaitosType,
    isChecked: boolean,
    handleClick: (value: OppilaitosType[], addCheck: boolean) => () => void,
    lang: string,
    disabled: boolean,
) => {
    const labelId = `transfer-list-all-item-${oppilaitos?.name[lang as keyof TextType]}-label`;

    let style = styles['multiselect-listitem'];
    if (disabled) style = styles['activated-listitem'];
    else if (isChecked) style = styles['multiselect-listitem-checked'];

    return (
        <ListItem
            key={oppilaitos.oid}
            role="listitem"
            onClick={handleClick([oppilaitos], !isChecked)}
            className={style}
        >
            <ListItemText
                id={labelId}
                primary={oppilaitos?.name[lang as keyof TextType]}
            />
            <ListItemIcon className={styles['multiselect-listitem-icon']}>
                {!disabled && (
                    <Checkbox
                        checked={isChecked}
                        tabIndex={-1}
                        disableRipple
                        inputProps={{
                            'aria-labelledby': labelId,
                        }}
                        className={
                            isChecked
                                ? styles['multiselect-listitem-checkbox-selected']
                                : styles['multiselect-listitem-checkbox']
                        }
                        checkedIcon={<CheckIcon />}
                    />
                )}
            </ListItemIcon>
        </ListItem>
    );
};

const oppilaitosGroup = (
    groupname: TextType,
    oppilaitokset: OppilaitosType[],
    checked: OppilaitosSetType,
    groupChecked: 0 | 1 | 2,
    selectableGroups: boolean,
    handleToggle: (value: OppilaitosType[], addCheck: boolean) => () => void,
    lang: string,
    expanded: Record<string, boolean>,
    handleExpand: (accordion: string, open?: boolean) => void,
    disabled: boolean,
) => {
    const expandedState = expanded[groupname.fi] || false;
    const style = !disabled
        ? styles['group-accordion']
        : styles['group-accordion-activated'];

    return (
        <Accordion
            key={`${groupname.fi}_${oppilaitokset[0]?.oid}`}
            disableGutters
            sx={{boxShadow: 0}}
            className={style}
            expanded={expandedState}
            onClick={(e) => {
                e.stopPropagation();
                if (disabled) return;
                if (!expandedState && groupChecked !== 2)
                    handleExpand(groupname.fi, true);
            }}
            onChange={handleToggle(
                oppilaitokset,
                groupChecked === 1 ? true : !groupChecked,
            )}
        >
            <AccordionSummary
                expandIcon={
                    <ExpandMoreRounded
                        sx={{
                            border: '1px solid',
                            borderRadius: '50%',
                        }}
                        onClick={(e) => {
                            e.stopPropagation();
                            handleExpand(groupname.fi, !expandedState);
                        }}
                    />
                }
                className={styles['group-heading']}
                component="div"
            >
                {groupname[lang as keyof TextType]}
                {selectableGroups && (
                    <Checkbox
                        checked={groupChecked === 2}
                        indeterminate={groupChecked === 1}
                        checkedIcon={<CheckIcon />}
                        indeterminateIcon={<IndeterminateCheckBoxOutlinedIcon />}
                        tabIndex={-1}
                        disableRipple
                        onClick={(e) => {
                            e.stopPropagation();
                            if (!expandedState && groupChecked !== 2)
                                handleExpand(groupname.fi, true);
                        }}
                        onChange={handleToggle(
                            oppilaitokset,
                            groupChecked === 1 ? true : !groupChecked,
                        )}
                        className={styles.groupCheckbox}
                    />
                )}
            </AccordionSummary>
            <AccordionDetails sx={{paddingBottom: 0, paddingRight: 0}}>
                {oppilaitokset.map((oppilaitos) =>
                    oppilaitosItem(
                        oppilaitos,
                        !!checked.grouped?.find((group) =>
                            group.oppilaitokset?.includes(oppilaitos),
                        ),
                        handleToggle,
                        lang,
                        disabled,
                    ),
                )}
            </AccordionDetails>
        </Accordion>
    );
};
function ItemsList({
    isLeft,
    allItems = getDefaultEmptySet(),
    disabled = false,
    filter,
    setFilter,
    checked,
    setChecked,
    itemsInGroups = true,
    label = '',
    labelModifiable = false,
    selectableGroups = false,
    formMethods,
}: ItemsListProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['aktivointi']);

    const [newGroupName, setNewGroupName] = useState<TextType>({fi: '', sv: ''});
    const [showNameInputField, setShowNameInputField] = useState<boolean>(false);
    const [expanded, setExpanded] = useState<Record<string, boolean>>({});

    const handleExpand = (accordion: string, open?: boolean) => {
        setExpanded((prev) => ({
            ...prev,
            [accordion]: (open !== undefined && open) || !prev[accordion],
        }));
    };

    const numberOfChecked = (items: OppilaitosSetType) =>
        itemsLength(itemsIntersection(checked, items));

    const handleToggle = (values: OppilaitosType[], addCheck: boolean) => () => {
        const newChecked = {...checked};
        values.forEach((value) => {
            if (!addCheck) {
                newChecked.grouped = newChecked.grouped
                    .map(
                        (group): OppilaitosGroupType => ({
                            ...group,
                            oppilaitokset: group.oppilaitokset.filter(
                                (ol) => ol.oid !== value.oid,
                            ),
                        }),
                    )
                    .filter((group) => group.oppilaitokset.length !== 0);

                newChecked.ungrouped[0].oppilaitokset =
                    newChecked.ungrouped[0]?.oppilaitokset.filter((ol) => ol !== value);
            } else {
                const valueGroup = allItems?.grouped.find((group) =>
                    group.oppilaitokset.includes(value),
                );
                if (valueGroup) {
                    const checkedGroup = newChecked.grouped.find(
                        (group) => group.name === valueGroup?.name,
                    );
                    newChecked.grouped = newChecked.grouped.filter(
                        (group) => group.name !== valueGroup?.name,
                    );

                    if (checkedGroup) {
                        checkedGroup.oppilaitokset.push(value);
                        newChecked.grouped.push(checkedGroup);
                    } else {
                        newChecked.grouped.push({
                            ...valueGroup,
                            oppilaitokset: [value],
                        } as OppilaitosGroupType);
                    }
                } else {
                    newChecked.ungrouped[0]?.oppilaitokset.push(value);
                }
            }
        });
        setChecked(newChecked);
    };

    const handleToggleAll = () => () => {
        if (numberOfChecked(allItems) === itemsLength(allItems)) {
            setChecked(getDefaultEmptySet());
        } else {
            // Spread syntax needed below to prevent shared references between 'allItems' and 'checked'.
            setChecked({
                grouped: {...allItems}.grouped,
                ungrouped: [{...{...allItems}.ungrouped[0]}],
            });
        }
    };

    const sorted = useMemo(() => sortItems(allItems, lang), [allItems, lang]);

    const items = useMemo(
        () => filterItems(sorted, filter, lang),
        [sorted, filter, lang],
    );

    const indeterminateChecked =
        numberOfChecked(allItems) !== itemsLength(allItems) &&
        numberOfChecked(allItems) !== 0;
    const allChecked =
        numberOfChecked(allItems) === itemsLength(allItems) &&
        itemsLength(allItems) !== 0;

    const renderItems = () =>
        itemsInGroups ? (
            <>
                {items?.grouped?.map((olGroup) => {
                    if (olGroup.oppilaitokset.length === 0) return null;
                    const checkedGroup = checked.grouped.find(
                        (chGroup) => chGroup.id === olGroup.id,
                    );

                    // Check if some of the oppilaitoses are checked, save the value in checkedValue.
                    // Not checked: 0, indeterminate: 1, checked: 2.
                    const checkedArray = olGroup.oppilaitokset.map(
                        (ol) => checkedGroup?.oppilaitokset.includes(ol) || false,
                    );
                    let checkedValue: 0 | 1 | 2;
                    if (checkedArray.every((value) => value === true)) checkedValue = 2;
                    else if (checkedArray.every((value) => value === false))
                        checkedValue = 0;
                    else checkedValue = 1;

                    return oppilaitosGroup(
                        olGroup.name,
                        olGroup.oppilaitokset,
                        checked,
                        checkedValue,
                        selectableGroups,
                        handleToggle,
                        lang,
                        expanded,
                        handleExpand,
                        disabled,
                    );
                })}
                {items?.ungrouped?.[0]?.oppilaitokset?.map((oppilaitos: OppilaitosType) =>
                    oppilaitosItem(
                        oppilaitos,
                        checked.ungrouped?.[0]?.oppilaitokset?.includes(oppilaitos),
                        handleToggle,
                        lang,
                        disabled,
                    ),
                )}
            </>
        ) : (
            <>
                {flattenItems(items, lang).map(
                    (oppilaitos) =>
                        oppilaitos &&
                        oppilaitosItem(
                            oppilaitos,
                            flattenItems(checked, lang).includes(oppilaitos),
                            handleToggle,
                            lang,
                            disabled,
                        ),
                )}
            </>
        );

    return (
        <fieldset>
            {showNameInputField ? (
                <div className={styles.nameSetting}>
                    <div className={styles.nameSettingFields}>
                        <GenericTextField
                            value={newGroupName.fi}
                            label={t('alueen-nimi-suomeksi', {ns: 'aluejako'})}
                            onChange={(value: string) =>
                                setNewGroupName({...newGroupName, fi: value})
                            }
                        />
                        <GenericTextField
                            value={newGroupName.sv}
                            label={t('alueen-nimi-ruotsiksi', {ns: 'aluejako'})}
                            onChange={(value: string) =>
                                setNewGroupName({...newGroupName, sv: value})
                            }
                        />
                    </div>
                    <div className={styles.nameSettingButtons}>
                        <IconButton
                            className="icon-button"
                            aria-label="edit name"
                            component="span"
                            onClick={() => {
                                setNewGroupName({
                                    fi:
                                        formMethods?.getValues().name_fi ||
                                        newGroupName.fi,
                                    sv:
                                        formMethods?.getValues().name_sv ||
                                        newGroupName.sv,
                                });
                                setShowNameInputField(false);
                            }}
                        >
                            <CloseIcon />
                        </IconButton>
                        <IconButton
                            className="icon-button"
                            aria-label="save name"
                            component="span"
                            onClick={() => {
                                formMethods?.setValue('name_fi', newGroupName.fi, {
                                    shouldDirty: true,
                                });
                                formMethods?.setValue('name_sv', newGroupName.sv, {
                                    shouldDirty: true,
                                });
                                setShowNameInputField(false);
                            }}
                        >
                            <CheckIcon />
                        </IconButton>
                    </div>
                </div>
            ) : (
                <>
                    {isLeft && (
                        <>
                            <div className={styles['multiselect-button']}>
                                <button
                                    type="button"
                                    onClick={handleToggleAll()}
                                    className={styles['multiselect-selectall-btn']}
                                    disabled={itemsLength(allItems) === 0}
                                >
                                    {indeterminateChecked || !allChecked
                                        ? t('valitse-kaikki')
                                        : t('poista-kaikki')}
                                </button>
                            </div>
                            <div className={styles['multiselect-search']}>
                                <GenericTextField
                                    value={filter}
                                    label=""
                                    showLabel={false}
                                    onChange={setFilter}
                                    fullWidth
                                    placeholder={
                                        isLeft
                                            ? t('hae-placeholder-left')
                                            : t('hae-placeholder-right')
                                    }
                                    clearButton
                                />
                            </div>
                        </>
                    )}
                    <div className={styles.legendContainer}>
                        <legend>
                            {label ||
                                (isLeft ? t('hae-title-left') : t('hae-title-right'))}
                        </legend>
                        {labelModifiable && (
                            <IconButton
                                className="icon-button"
                                aria-label="edit name"
                                component="span"
                                onClick={() => {
                                    const vals = formMethods?.getValues?.();
                                    setNewGroupName({
                                        fi: vals?.name_fi ?? '',
                                        sv: vals?.name_sv ?? '',
                                    });
                                    setShowNameInputField(true);
                                }}
                            >
                                <EditIcon />
                            </IconButton>
                        )}
                    </div>
                </>
            )}
            <List
                dense
                component="div"
                role="list"
                className={
                    disabled ? styles['activated-list'] : styles['multiselect-list']
                }
            >
                {renderItems()}
                <ListItem />
            </List>
        </fieldset>
    );
}

export default ItemsList;
