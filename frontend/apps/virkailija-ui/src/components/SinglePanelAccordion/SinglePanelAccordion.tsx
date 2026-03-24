import {
    ReactElement,
    ReactNode,
    SyntheticEvent,
    useCallback,
    useState,
    useId,
} from 'react';
import MuiAccordion from '@mui/material/Accordion';
import MuiAccordionSummary from '@mui/material/AccordionSummary';
import MuiAccordionDetails from '@mui/material/AccordionDetails';
import Avatar from '@mui/material/Avatar';
import ExpandMoreRounded from '@mui/icons-material/ExpandMore';
import {useTranslation} from 'react-i18next';
import styles from './SinglePanelAccordion.module.css';

interface SinglePanelAccordionProps {
    title?: ReactNode;
    children: ReactElement | ReactElement[];
    borders?: boolean;
    fullWidth?: boolean;
    dataCollection?: boolean;
    alignLeft?: boolean;
    alignColumn?: boolean;
    openText?: string;
    closeText?: string;
    specialHandlingIfChildHasNoChildren?: boolean;
}

function SinglePanelAccordion({
    title = null,
    children,
    borders = true,
    fullWidth = true,
    dataCollection = false,
    alignLeft = !title,
    alignColumn = !alignLeft,
    openText,
    closeText,
    specialHandlingIfChildHasNoChildren,
}: SinglePanelAccordionProps) {
    const {t} = useTranslation(['yleiset']);
    const [expanded, setExpanded] = useState<string | false>(false);
    const pandelId = useId();

    const handleChange = useCallback(
        (panel: string) => (event: SyntheticEvent, isExpanded: boolean) => {
            setExpanded(isExpanded ? panel : false);
        },
        [],
    );

    const rootContainerStyles = [
        !borders && styles['accordion-root-no-borders'],
        !fullWidth && styles['accordion-root-shrink'],
        dataCollection && styles['accordion-data-collection'],
    ]
        .filter(Boolean)
        .join(' ');

    const summaryItemStyles = alignLeft
        ? {
              content:
                  styles[
                      alignColumn
                          ? 'accordion-summary-item-shrink-column'
                          : 'accordion-summary-item-shrink'
                  ],
          }
        : {content: styles['accordion-summary-item']};

    if (specialHandlingIfChildHasNoChildren) {
        if (children.props.children.length === 0) {
            return <></>;
        }
    }

    return (
        <MuiAccordion
            key={`key_${pandelId}`}
            disableGutters
            square
            elevation={0}
            expanded={expanded === pandelId}
            onChange={handleChange(pandelId)}
            classes={{root: styles['accordion-root']}}
            className={rootContainerStyles}
        >
            <MuiAccordionSummary
                aria-label={`${expanded ? t('sulje') : t('avaa')}: ${title ?? ''}`}
                aria-controls={pandelId}
                id={pandelId}
                component="summary"
                data-testid="avaa-sulje"
                expandIcon={
                    <Avatar className={styles['accordion-expand-more-avatar']}>
                        <ExpandMoreRounded className={styles['accordion-expand-more']} />
                    </Avatar>
                }
                classes={summaryItemStyles}
                className={
                    styles[
                        alignLeft
                            ? 'accordion-summary-container-left'
                            : 'accordion-summary-container'
                    ]
                }
            >
                {title && dataCollection ? (
                    <h3 className={styles['accordion-title-h3']}>{title}</h3>
                ) : (
                    <div className={styles['accordion-title-text']}>{title}</div>
                )}
                <div
                    className={
                        styles[
                            alignColumn
                                ? 'accordion-expand-more-text-column'
                                : 'accordion-expand-more-text'
                        ]
                    }
                >
                    {expanded === pandelId
                        ? closeText || t('sulje')
                        : openText || t('avaa')}
                </div>
            </MuiAccordionSummary>
            <MuiAccordionDetails
                className={`${dataCollection ? styles['compact-details'] : ''}`}
            >
                {children}
            </MuiAccordionDetails>
        </MuiAccordion>
    );
}

export default SinglePanelAccordion;
