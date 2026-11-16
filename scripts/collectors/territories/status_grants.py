"""Federal assistance is nonpermit context, even when a data center is expressly funded."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
def classify(r,cutoff,perm,no,app,obs):
 if r.get('dataset')=='Interior insular data-center financial assistance':
  return no('Award for procurement or maintenance; no site-specific permit, zoning or NEPA approval.','observation')
 return None
