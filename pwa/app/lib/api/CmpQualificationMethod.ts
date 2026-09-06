import { CmpQualificationMethod } from '~/api/tba/read';

export const CMP_QUALIFICATION_METHOD_LABELS: Record<
  CmpQualificationMethod,
  string
> = {
  [CmpQualificationMethod.DISTRICT_POINTS]: 'District Points',
  [CmpQualificationMethod.WAITLIST]: 'Waitlist',
  [CmpQualificationMethod.ORIGINAL_AND_SUSTAINING]: 'Original & Sustaining',
  [CmpQualificationMethod.HALL_OF_FAME]: 'Hall of Fame',
  [CmpQualificationMethod.PRIOR_YEAR_CMP_WINNER]: 'Prior Year CMP Winner',
  [CmpQualificationMethod.PRIOR_YEAR_CMP_IMPACT]: 'Prior Year CMP Impact',
  [CmpQualificationMethod.PRIOR_YEAR_CMP_ENGINEERING_INSPIRATION]:
    'Prior Year CMP Engineering Inspiration',
  [CmpQualificationMethod.REGIONAL_WINNER]: 'Regional Winner',
  [CmpQualificationMethod.REGIONAL_IMPACT]: 'Regional Impact',
  [CmpQualificationMethod.REGIONAL_ENGINEERING_INSPIRATION]:
    'Regional Engineering Inspiration',
  [CmpQualificationMethod.REGIONAL_WILDCARD]: 'Regional Wildcard',
  [CmpQualificationMethod.LATE_REGIONAL_WINNER]: 'Late Regional Winner',
  [CmpQualificationMethod.LATE_REGIONAL_IMPACT]: 'Late Regional Impact',
  [CmpQualificationMethod.LATE_REGIONAL_ENGINEERING_INSPIRATION]:
    'Late Regional Engineering Inspiration',
  [CmpQualificationMethod.LATE_REGIONAL_WILDCARD]: 'Late Regional Wildcard',
  [CmpQualificationMethod.DCMP_WINNER]: 'DCMP Winner',
  [CmpQualificationMethod.DCMP_IMPACT]: 'DCMP Impact',
  [CmpQualificationMethod.DCMP_ENGINEERING_INSPIRATION]:
    'DCMP Engineering Inspiration',
  [CmpQualificationMethod.DCMP_ROOKIE_ALL_STAR]: 'DCMP Rookie All Star',
};
