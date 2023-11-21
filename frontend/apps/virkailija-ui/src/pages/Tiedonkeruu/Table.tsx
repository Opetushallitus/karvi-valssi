import {useTranslation} from 'react-i18next';
import {KyselyCollectionType} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import Table from '@mui/material/Table';
import {TableBody, TableCell, TableHead, TableRow} from '@mui/material';
import {formatDate} from '@cscfi/shared/utils/helpers'; // also notice frontend/shared/src/theme.ts
import GuardedComponentWrapper, {
    ValssiUserLevel,
} from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import styles from './Tiedonkeruu.module.css'; // also notice frontend/shared/src/theme.ts

interface KyselyTableProps {
    kysely: KyselyCollectionType | null;
}
function Tables({kysely}: KyselyTableProps) {
    const {t} = useTranslation(['tiedonkeruun-seuranta']);

    return (
        <div className={styles['tables-wrapper']}>
            <div className={styles['left-table-wrapper']}>
                <GuardedComponentWrapper
                    allowedValssiRoles={[ValssiUserLevel.TOTEUTTAJA]}
                >
                    <Table size="small" className={styles['left-table']}>
                        <TableHead>
                            <TableRow>
                                <TableCell> </TableCell>
                                <TableCell variant="head">{t('lahetetty')}</TableCell>
                                <TableCell variant="head">{t('vastannut')}</TableCell>
                                <TableCell variant="head">
                                    {t('vastausprosentti')}
                                </TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            <TableRow>
                                <TableCell variant="head" component="th" scope="row">
                                    {t('vastaajat')}
                                </TableCell>
                                <TableCell>{kysely?.statistics?.sent_count}</TableCell>
                                <TableCell>
                                    {kysely?.statistics?.answered_count}
                                </TableCell>
                                <TableCell>{kysely?.statistics?.answer_pct} %</TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </GuardedComponentWrapper>

                <GuardedComponentWrapper
                    allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}
                >
                    <Table size="small" className={styles['left-table']}>
                        <TableHead>
                            <TableRow>
                                <TableCell> </TableCell>
                                <TableCell variant="head">{t('kaytosssa')}</TableCell>
                                <TableCell variant="head">{t('lahetetty')}</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            <TableRow>
                                <TableCell variant="head" component="th" scope="row">
                                    {t('toimipaikat')}
                                </TableCell>
                                <TableCell>
                                    {kysely?.toimipaikka_statistics?.in_use_count ?? '-'}
                                </TableCell>
                                <TableCell>
                                    {kysely?.toimipaikka_statistics?.sent_count ?? '-'}
                                </TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                    <Table size="small" className={styles['left-table']}>
                        <TableHead>
                            <TableRow>
                                <TableCell> </TableCell>
                                <TableCell variant="head">{t('lahetetty')}</TableCell>
                                <TableCell variant="head">{t('vastannut')}</TableCell>
                                <TableCell variant="head">
                                    {t('vastausprosentti')}
                                </TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            <TableRow>
                                <TableCell variant="head" component="th" scope="row">
                                    {t('vastaajat')}
                                </TableCell>
                                <TableCell>
                                    {kysely?.vastaaja_statistics?.sent_count}
                                </TableCell>
                                <TableCell>
                                    {kysely?.vastaaja_statistics?.answered_count}
                                </TableCell>
                                <TableCell>
                                    {kysely?.vastaaja_statistics?.answer_pct} %
                                </TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </GuardedComponentWrapper>
            </div>

            <div className={styles['right-table-wrapper']}>
                <table className={styles['right-table']}>
                    <tbody>
                        <tr>
                            <th>{t('kysely-kaynnistetty')}</th>
                            <td>{formatDate(kysely?.voimassa_alkupvm)}</td>
                        </tr>
                        <tr>
                            <th>{t('kysely-sulkeutuu')}</th>
                            <td>{formatDate(kysely?.voimassa_loppupvm)}</td>
                        </tr>
                        <tr>
                            <th>{t('viimeinen-vastaus-saapunut')}</th>
                            <td>{formatDate(kysely?.latest_answer_date)}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}
export default Tables;
